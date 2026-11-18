"""Shared helpers for the tc-create pack: textures, cuboid models, item files.

Every texture and model here is drawn from scratch in Create's style (andesite
alloy, spruce casing, brass, iron). Create's own assets are All Rights
Reserved, so none are copied.
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent  # pack/
ASSETS = ROOT / "assets"
NS = "create"


def hexc(s: str, a: int = 255) -> tuple[int, int, int, int]:
    s = s.lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)


def shade(c, f: float):
    return (max(0, min(255, round(c[0] * f))), max(0, min(255, round(c[1] * f))),
            max(0, min(255, round(c[2] * f))), c[3])


# ---------------------------------------------------------------- palettes

ALLOY = [hexc(c) for c in ("a3a39a", "9a9a91", "aeada4", "8f8f87", "b7b6ad")]
ALLOY_DARK = [hexc(c) for c in ("6e6e68", "77776f", "65655f")]
STONE = [hexc(c) for c in ("8c8c86", "838380", "95958f", "7b7b77", "9e9e98")]
SPRUCE = [hexc(c) for c in ("7a5a3a", "6e5034", "85633f", "634830")]
SPRUCE_DARK = [hexc(c) for c in ("4f3a26", "584129", "463321")]
WOOD = [hexc(c) for c in ("9c7a4c", "8f6f44", "a88553", "84653f")]
IRON = [hexc(c) for c in ("d6d6d6", "cbcbcb", "dfdfdf", "c2c2c2")]
IRON_DARK = [hexc(c) for c in ("8f8f8f", "9b9b9b", "848484")]
BRASS = [hexc(c) for c in ("e3ac48", "d69d3b", "edbd5a", "c98f33")]
BRASS_DARK = [hexc(c) for c in ("9c6a22", "a8752a", "8f601e")]
COPPER = [hexc(c) for c in ("c56d48", "b8603f", "d17b53", "a95637")]
MAGENTA = [hexc(c) for c in ("a447b5", "943da4", "b154c2", "86358f")]
GRANITE = [hexc(c) for c in ("9a8f86", "8d827a", "a59b92", "807770", "b0a69c")]
RUBBER = [hexc(c) for c in ("3a3a3e", "333337", "414146", "2d2d31")]


class Tex:
    """A 16x16 (or larger) RGBA texture with seeded pixel-art painters."""

    def __init__(self, name: str, size: int = 16, seed: int | None = None):
        self.name = name
        self.size = size
        self.img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        self.px = self.img.load()
        self.rng = random.Random(seed if seed is not None else hash(name) & 0xFFFF)

    def set(self, x: int, y: int, c):
        if 0 <= x < self.size and 0 <= y < self.size:
            self.px[x, y] = c

    def get(self, x: int, y: int):
        return self.px[x, y]

    def fill(self, x0, y0, x1, y1, palette, weights=None):
        """Noise-fills [x0, x1) x [y0, y1) from a palette."""
        for y in range(y0, y1):
            for x in range(x0, x1):
                self.set(x, y, self.rng.choices(palette, weights=weights)[0])

    def solid(self, x0, y0, x1, y1, c):
        for y in range(y0, y1):
            for x in range(x0, x1):
                self.set(x, y, c)

    def frame(self, x0, y0, x1, y1, c, w=1):
        for i in range(w):
            for x in range(x0, x1):
                self.set(x, y0 + i, c)
                self.set(x, y1 - 1 - i, c)
            for y in range(y0, y1):
                self.set(x0 + i, y, c)
                self.set(x1 - 1 - i, y, c)

    def bevel(self, x0, y0, x1, y1, f_hi=1.12, f_lo=0.82):
        """Lightens the top/left edge and darkens the bottom/right one."""
        for x in range(x0, x1):
            self.set(x, y0, shade(self.get(x, y0), f_hi))
            self.set(x, y1 - 1, shade(self.get(x, y1 - 1), f_lo))
        for y in range(y0, y1):
            self.set(x0, y, shade(self.get(x0, y), f_hi))
            self.set(x1 - 1, y, shade(self.get(x1 - 1, y), f_lo))

    def planks(self, x0, y0, x1, y1, palette, dark, board=4, vertical=False):
        """Boards with dark seams and a little grain."""
        span = (x1 - x0) if vertical else (y1 - y0)
        for i in range(0, span, board):
            if vertical:
                self.fill(x0 + i, y0, min(x1, x0 + i + board), y1, palette)
                for y in range(y0, y1):
                    self.set(x0 + i, y, self.rng.choice(dark))
            else:
                self.fill(x0, y0 + i, x1, min(y1, y0 + i + board), palette)
                for x in range(x0, x1):
                    self.set(x, y0 + i, self.rng.choice(dark))
                # a nail / knot now and then
                kx = self.rng.randrange(x0 + 1, x1 - 1)
                self.set(kx, y0 + i + board // 2, self.rng.choice(dark))

    def disc(self, cx, cy, r, palette, ring=None):
        for y in range(self.size):
            for x in range(self.size):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                if d <= r:
                    self.set(x, y, self.rng.choice(palette))
                    if ring is not None and d > r - 1:
                        self.set(x, y, self.rng.choice(ring))

    def save(self):
        out = ASSETS / NS / "textures" / f"{self.name}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        self.img.save(out)
        return f"{NS}:{self.name}"


# ---------------------------------------------------------------- models

FACES = ("north", "south", "east", "west", "up", "down")


def auto_uv(face: str, f, t):
    """Box-projected UV for a face of the cuboid from f to t (model px)."""
    x0, y0, z0 = f
    x1, y1, z1 = t
    if face in ("north", "south"):
        u = (x0, x1) if face == "south" else (16 - x1, 16 - x0)
        v = (16 - y1, 16 - y0)
    elif face in ("east", "west"):
        u = (16 - z1, 16 - z0) if face == "east" else (z0, z1)
        v = (16 - y1, 16 - y0)
    else:
        u = (x0, x1)
        v = (z0, z1) if face == "up" else (16 - z1, 16 - z0)

    def wrap(a, b):
        # keep inside 0..16 for parts larger than a block
        lo = a % 16 if a < 0 or a > 16 else a
        w = min(b - a, 16)
        if lo + w > 16:
            lo = 16 - w
        return lo, lo + w

    u = wrap(*u)
    v = wrap(*v)
    return [round(u[0], 3), round(v[0], 3), round(u[1], 3), round(v[1], 3)]


class Model:
    def __init__(self, name: str, textures: dict[str, str], tinted: bool = False, ao: bool = False):
        self.name = name
        self.textures = dict(textures)
        self.tinted = tinted
        self.ao = ao
        self.elements: list[dict] = []
        self.display: dict = {}

    def box(self, f, t, tex, faces=FACES, rot=None, uv=None, cull=False, tex_faces=None):
        """Adds a cuboid. tex is a texture key ('#side'); tex_faces overrides it
        per face; rot = (axis, angle, origin) with angle in -45..45."""
        el = {"from": [round(v, 4) for v in f], "to": [round(v, 4) for v in t], "faces": {}}
        if rot is not None:
            axis, angle, origin = rot
            if angle != 0:
                el["rotation"] = {"angle": angle, "axis": axis, "origin": list(origin)}
        for face in faces:
            key = (tex_faces or {}).get(face, tex)
            fd = {"uv": (uv or {}).get(face) or auto_uv(face, f, t), "texture": key}
            if self.tinted:
                fd["tintindex"] = 0
            el["faces"][face] = fd
        self.elements.append(el)
        return el

    def spoke(self, angle: float, r0: float, r1: float, half_w: float, y0: float, y1: float, tex,
              tex_faces=None, faces=FACES):
        """A box pointing out from the Y axis through (8, 8) at `angle` degrees
        (0 = +x, measured toward -z, Create's turning sense), from radius r0 to r1."""
        base = round(angle / 90.0) * 90
        rel = angle - base
        if rel > 45 or rel < -45:
            raise ValueError(angle)
        b = int(base) % 360
        if b == 0:
            f, t = (8 + r0, y0, 8 - half_w), (8 + r1, y1, 8 + half_w)
        elif b == 90:
            f, t = (8 - half_w, y0, 8 - r1), (8 + half_w, y1, 8 - r0)
        elif b == 180:
            f, t = (8 - r1, y0, 8 - half_w), (8 - r0, y1, 8 + half_w)
        else:
            f, t = (8 - half_w, y0, 8 + r0), (8 + half_w, y1, 8 + r1)
        # element rotation about y: positive angle turns +x toward -z in model
        # files ("angle" follows the right hand about +y), the same sense as
        # `angle` here
        return self.box(f, t, tex, rot=("y", rel, (8, 8, 8)) if rel else None, tex_faces=tex_faces, faces=faces)

    def write(self, sub="part"):
        data = {"textures": self.textures, "elements": self.elements}
        if not self.ao:
            data["ambientocclusion"] = False
        if self.display:
            data["display"] = self.display
        out = ASSETS / NS / "models" / sub / f"{self.name}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(data, indent=1) + "\n")
        return f"{NS}:{sub}/{self.name}"


def item_def(path: str, model: str, tinted: bool = False):
    """assets/create/items/<path>.json pointing at a model; a tinted part gets
    custom model data color 0 (white by default, which the shader ignores)."""
    m = {"type": "minecraft:model", "model": model}
    if tinted:
        m["tints"] = [{"type": "minecraft:custom_model_data", "index": 0, "default": 16777215}]
    out = ASSETS / NS / "items" / f"{path}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"model": m}, indent=1) + "\n")
    return f"{NS}:{path}"


def flat_item_model(name: str, texture: str):
    out = ASSETS / NS / "models" / "item" / f"{name}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"parent": "minecraft:item/generated", "textures": {"layer0": texture}}, indent=1) + "\n")
    return f"{NS}:item/{name}"


# Display transforms for block-like icons (the vanilla block ones).
BLOCK_DISPLAY = {
    "gui": {"rotation": [30, 225, 0], "translation": [0, 0, 0], "scale": [0.625, 0.625, 0.625]},
    "ground": {"rotation": [0, 0, 0], "translation": [0, 3, 0], "scale": [0.25, 0.25, 0.25]},
    "fixed": {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [0.5, 0.5, 0.5]},
    "thirdperson_righthand": {"rotation": [75, 45, 0], "translation": [0, 2.5, 0], "scale": [0.375, 0.375, 0.375]},
    "firstperson_righthand": {"rotation": [0, 45, 0], "translation": [0, 0, 0], "scale": [0.40, 0.40, 0.40]},
    "firstperson_lefthand": {"rotation": [0, 225, 0], "translation": [0, 0, 0], "scale": [0.40, 0.40, 0.40]},
}


def scaled_display(scale: float):
    d = json.loads(json.dumps(BLOCK_DISPLAY))
    for v in d.values():
        v["scale"] = [s * scale for s in v["scale"]]
    return d
