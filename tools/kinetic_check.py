#!/usr/bin/env python3
"""Checks the spin-color round trip and cogwheel meshing offline.

    python3 tools/kinetic_check.py

1. kineticTint (tc/render.tc) packs axis, speed, large flag and pivot into a
   color; the shader (pack/.../core/item.vsh) unpacks it. This runs both in
   Python for many blocks, camera positions and vertices and checks the
   shader finds the right pivot block and speed.
2. Meshing: with the shader's angle (Create's: ticks * rpm * 0.3 plus 22.5
   on even blocks, 11.25 for large cogs) and the pack's teeth (small: every
   45 degrees from 0, large: every 22.5 from 0), the teeth of cogs that touch
   must never overlap while they turn at their ratio. Checked by sampling
   the angle between the nearest teeth at the contact point.
"""

from __future__ import annotations

import math
import random

AX = {"x": 0, "y": 1, "z": 2}
CROSS = {"x": (1, 2), "y": (0, 2), "z": (0, 1)}


def tint(axis: str, rpm: float, large: int, block: tuple[int, int, int]) -> int:
    a, b = CROSS[axis]
    pa = block[a] % 4
    pb = block[b] % 4
    half = max(-1024, min(1023, round(rpm * 2)))
    if half < 0:
        half += 2048
    return 262144 + AX[axis] * 65536 + large * 32768 + pa * 8192 + pb * 2048 + half


def shader_decode(code: int, vertex_world: tuple[float, float, float], cam_block: tuple[int, int, int]):
    """item.vsh kinetic_turn, minus the turning: returns (axis, rpm, large, pivot block, offset)."""
    assert (code >> 18) == 1
    axis = (code >> 16) & 3
    large = (code >> 15) & 1
    pa = (code >> 13) & 3
    pb = (code >> 11) & 3
    sp = code & 2047
    if sp >= 1024:
        sp -= 2048
    rpm = sp * 0.5
    ia = 1 if axis == 0 else 0
    ib = 1 if axis == 2 else 2
    rel = [vertex_world[i] - cam_block[i] for i in range(3)]
    ba, bb = cam_block[ia], cam_block[ib]
    ma = (pa - ba) & 3
    mb = (pb - bb) & 3
    na = round((rel[ia] - 0.5 - ma) / 4.0)
    nb = round((rel[ib] - 0.5 - mb) / 4.0)
    block_a = ba + ma + 4 * int(na)
    block_b = bb + mb + 4 * int(nb)
    off = 22.5 if ((block_a + block_b) & 1) == 0 else (11.25 if large else 0.0)
    return axis, rpm, large, (block_a, block_b), off


def check_roundtrip(n=20000) -> int:
    rng = random.Random(1)
    bad = 0
    for _ in range(n):
        block = tuple(rng.randint(-3000, 3000) for _ in range(3))
        axis = rng.choice("xyz")
        rpm = rng.choice([0, 0.5, 1, 2, 4, 8, 16, 32, 64, 128, 256]) * rng.choice([1, -1])
        large = rng.randint(0, 1)
        code = tint(axis, rpm, large, block)
        # a vertex up to 1.9 blocks across the axis from the center, anywhere along it
        v = [block[i] + 0.5 for i in range(3)]
        a, b = CROSS[axis]
        v[a] += rng.uniform(-1.9, 1.9)
        v[b] += rng.uniform(-1.9, 1.9)
        v[AX[axis]] += rng.uniform(-0.5, 0.5)
        cam = tuple(block[i] + rng.randint(-60, 60) for i in range(3))
        ax, r, lg, piv, _ = shader_decode(code, tuple(v), cam)
        if ax != AX[axis] or r != rpm or lg != large or piv != (block[a], block[b]):
            bad += 1
            if bad < 5:
                print("roundtrip mismatch", block, axis, rpm, large, cam, v, "->", ax, r, lg, piv)
    print(f"round trip: {n - bad}/{n} ok")
    return bad


def angle_of(block, axis, rpm, large, ticks):
    a, b = CROSS[axis]
    off = 22.5 if ((block[a] + block[b]) & 1) == 0 else (11.25 if large else 0.0)
    return (ticks * rpm * 0.3 + off) % 360


def tooth_gap(angle_teeth: float, step: float, contact_dir: float) -> float:
    """Signed angle from contact direction to the nearest tooth (degrees)."""
    d = (contact_dir - angle_teeth) % step
    return d if d <= step / 2 else d - step


def world_dir_angle(axis: str, vec2: tuple[float, float]) -> float:
    """The model angle (Create's turning sense, right-handed about +axis) of a
    direction in the plane across the axis. For y the plane is (z, x)."""
    u, v = vec2
    if axis == "y":
        # a tooth at model angle t points at (cos t, -sin t) in (x, z)
        return math.degrees(math.atan2(-v, u)) % 360
    return math.degrees(math.atan2(v, u)) % 360


def check_mesh() -> int:
    bad = 0
    cases = []
    # small-small neighbours, ratio -1
    for axis in "xyz":
        a, b = CROSS[axis]
        for base in [(0, 0, 0), (3, -7, 11), (-5, 2, -9)]:
            other = list(base)
            other[a] += 1
            cases.append(("small-small", axis, base, tuple(other), 1, -1, 45, 45, 0, 0))
            # large-small diagonal, small turns -2x
            other = list(base)
            other[a] += 1
            other[b] += 1
            cases.append(("large-small", axis, base, tuple(other), 1, -2, 22.5, 45, 1, 0))
    for name, axis, b1, b2, rpm, ratio, step1, step2, l1, l2 in cases:
        a, b = CROSS[axis]
        dvec = (b2[a] - b1[a], b2[b] - b1[b])
        if axis == "y":
            # plane order for y is (x, z) in world; angle helper wants (x, z)
            pass
        dir12 = world_dir_angle(axis, dvec)
        dir21 = world_dir_angle(axis, (-dvec[0], -dvec[1]))
        worst = 0
        for t in range(0, 2400, 7):
            t1 = angle_of(b1, axis, rpm, l1, t)
            t2 = angle_of(b2, axis, rpm * ratio, l2, t)
            g1 = tooth_gap(t1, step1, dir12)
            g2 = tooth_gap(t2, step2, dir21)
            # meshing: where cog 1 has a tooth at the contact, cog 2 has a gap
            # there: their tooth offsets differ by half a tooth pitch measured
            # along the rim. Compare as arc lengths (radius ratio = pitch ratio).
            arc1 = g1 / step1
            arc2 = g2 / step2
            # teeth face each other across the contact: arc positions mirror
            s = (arc1 + arc2) % 1.0
            err = min(abs(s - 0.5), abs(s + 0.5), abs(s - 1.5))
            worst = max(worst, err)
        ok = worst < 0.02
        if not ok:
            bad += 1
        print(f"mesh {name:12s} axis {axis} {b1}->{b2}: worst {worst:.3f} pitch {'ok' if ok else 'CLASH'}")
    return bad


if __name__ == "__main__":
    n = check_roundtrip() + check_mesh()
    raise SystemExit(1 if n else 0)
