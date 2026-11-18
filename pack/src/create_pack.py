#!/usr/bin/env python3
"""Builds the tc-create resource pack's textures, models and item files.

    python3 pack/src/create_pack.py

Writes pack/assets/create/{textures,models,items}/ (the shader and pack.mcmeta
are hand-written). Every block is made of parts; each part is one item display
on the plot:

- a *spinning* part is modeled around the y axis through the block center
  (8, 8, 8) and tints every face with custom model data color 0. The plot
  turns the display to the block's axis and packs the speed into that color;
  the core shader (pack/assets/minecraft/shaders/core/item.vsh) spins it.
- a *static* part (casings, frames) is modeled facing north / up as noted and
  is turned by the plot.

Parts and their item ids are listed in PARTS at the end (tc/blocks.tc uses
the same names). Item icons for the kit are in ICONS.
"""

from __future__ import annotations

import json
import math

from pack_lib import (ALLOY, ALLOY_DARK, ASSETS, BRASS, BRASS_DARK, COPPER, GRANITE, IRON, IRON_DARK,
                      MAGENTA, NS, RUBBER, SPRUCE, SPRUCE_DARK, STONE, WOOD, BLOCK_DISPLAY, Model, Tex,
                      flat_item_model, hexc, item_def, scaled_display, shade)

PARTS: dict[str, str] = {}   # part name -> model id
ICONS: dict[str, str] = {}   # kit item name -> model id


# ================================================================ textures


def tex_shaft():
    t = Tex("block/shaft", seed=11)
    # side: alloy with two lengthwise grooves (the texture runs along v)
    t.fill(0, 0, 16, 16, ALLOY)
    for y in range(16):
        t.set(5, y, t.rng.choice(ALLOY_DARK))
        t.set(10, y, t.rng.choice(ALLOY_DARK))
        t.set(4, y, shade(t.get(4, y), 1.1))
    for x in range(16):
        if x % 4 == 0:
            t.set(x, 0, t.rng.choice(ALLOY_DARK))
    side = t.save()
    e = Tex("block/shaft_end", seed=12)
    e.fill(0, 0, 16, 16, ALLOY)
    e.frame(0, 0, 16, 16, ALLOY_DARK[0])
    e.solid(6, 6, 10, 10, ALLOY_DARK[1])
    e.bevel(1, 1, 15, 15)
    return side, e.save()


def tex_casing():
    """Andesite casing: an alloy frame with bolts round spruce boards."""
    t = Tex("block/andesite_casing", seed=21)
    t.planks(2, 2, 14, 14, SPRUCE, SPRUCE_DARK, board=4)
    t.fill(0, 0, 16, 2, ALLOY)
    t.fill(0, 14, 16, 16, ALLOY)
    t.fill(0, 0, 2, 16, ALLOY)
    t.fill(14, 0, 16, 16, ALLOY)
    t.bevel(0, 0, 16, 16, 1.15, 0.75)
    for (x, y) in ((1, 1), (14, 1), (1, 14), (14, 14)):
        t.set(x, y, ALLOY_DARK[0])
    for i in range(2, 14):
        t.set(i, 2, shade(t.get(i, 2), 0.7))
        t.set(2, i, shade(t.get(2, i), 0.7))
    casing = t.save()
    # a casing face with a round port for a shaft
    p = Tex("block/andesite_casing_port", seed=22)
    p.img.paste(t.img)
    p.px = p.img.load()
    p.disc(8, 8, 4.2, ALLOY_DARK, ring=[hexc("4a4a46")])
    p.disc(8, 8, 2.2, [hexc("2b2b29")])
    port = p.save()
    # the inside of a casing / dark backing
    d = Tex("block/casing_inner", seed=23)
    d.fill(0, 0, 16, 16, SPRUCE_DARK)
    inner = d.save()
    return casing, port, inner


def tex_brass_casing():
    t = Tex("block/brass_casing", seed=31)
    t.planks(2, 2, 14, 14, SPRUCE, SPRUCE_DARK, board=4, vertical=True)
    for (x0, y0, x1, y1) in ((0, 0, 16, 2), (0, 14, 16, 16), (0, 0, 2, 16), (14, 0, 16, 16)):
        t.fill(x0, y0, x1, y1, BRASS)
    t.bevel(0, 0, 16, 16, 1.12, 0.72)
    for (x, y) in ((1, 1), (14, 1), (1, 14), (14, 14)):
        t.set(x, y, BRASS_DARK[0])
    casing = t.save()
    p = Tex("block/brass_casing_port", seed=32)
    p.img.paste(t.img)
    p.px = p.img.load()
    p.disc(8, 8, 4.2, BRASS_DARK, ring=[hexc("6b4614")])
    p.disc(8, 8, 2.2, [hexc("2b2b29")])
    return casing, p.save()


def tex_cog():
    t = Tex("block/cogwheel", seed=41)
    # face: wood rings
    for y in range(16):
        for x in range(16):
            d = math.hypot(x + 0.5 - 8, y + 0.5 - 8)
            c = t.rng.choice(WOOD)
            if int(d) % 3 == 0:
                c = shade(c, 0.85)
            t.set(x, y, c)
    face = t.save()
    s = Tex("block/cogwheel_side", seed=42)
    s.fill(0, 0, 16, 16, SPRUCE)
    for x in range(16):
        s.set(x, 0, shade(s.get(x, 0), 1.15))
        s.set(x, 15, shade(s.get(x, 15), 0.75))
    side = s.save()
    h = Tex("block/cog_hub", seed=43)
    h.fill(0, 0, 16, 16, ALLOY)
    h.frame(0, 0, 16, 16, ALLOY_DARK[0])
    h.bevel(1, 1, 15, 15)
    return face, side, h.save()


def tex_crank():
    t = Tex("block/crank_handle", seed=51)
    t.fill(0, 0, 16, 16, WOOD)
    for y in range(0, 16, 3):
        for x in range(16):
            t.set(x, y, shade(t.get(x, y), 0.85))
    h = Tex("block/crank_grip", seed=52)
    h.fill(0, 0, 16, 16, [hexc("6b3d22"), hexc("5f361e"), hexc("77452a")])
    return t.save(), h.save()


def tex_iron():
    t = Tex("block/iron_part", seed=61)
    t.fill(0, 0, 16, 16, IRON)
    t.bevel(0, 0, 16, 16, 1.05, 0.8)
    d = Tex("block/iron_dark", seed=62)
    d.fill(0, 0, 16, 16, IRON_DARK)
    return t.save(), d.save()


def tex_press():
    t = Tex("block/press_head", seed=71)
    t.fill(0, 0, 16, 16, IRON)
    t.frame(0, 0, 16, 16, IRON_DARK[0])
    t.bevel(1, 1, 15, 15)
    for x in range(3, 13, 3):
        for y in range(3, 13, 3):
            t.set(x, y, IRON_DARK[1])
    return t.save()


def tex_motor():
    t = Tex("block/creative_motor", seed=81)
    t.fill(0, 0, 16, 16, MAGENTA)
    for y in range(2, 16, 3):
        for x in range(16):
            t.set(x, y, shade(t.get(x, y), 0.7))
    t.bevel(0, 0, 16, 16, 1.2, 0.7)
    body = t.save()
    c = Tex("block/creative_motor_cap", seed=82)
    c.fill(0, 0, 16, 16, IRON)
    c.disc(8, 8, 5.5, MAGENTA, ring=[hexc("5e2367")])
    c.disc(8, 8, 2.5, IRON_DARK)
    return body, c.save()


def tex_millstone():
    t = Tex("block/millstone_side", seed=91)
    t.fill(0, 0, 16, 16, GRANITE)
    for x in range(16):
        t.set(x, 0, shade(t.get(x, 0), 1.15))
    side = t.save()
    top = Tex("block/millstone_top", seed=92)
    top.fill(0, 0, 16, 16, GRANITE)
    # grinding grooves: spokes from the center
    for a in range(0, 360, 45):
        for r in range(2, 8):
            x = 8 + round(r * math.cos(math.radians(a)))
            y = 8 + round(r * math.sin(math.radians(a)))
            top.set(x, y, shade(top.get(x, y), 0.7))
    top.disc(8, 8, 1.6, [hexc("3b3632")])
    return side, top.save()


def tex_fan():
    t = Tex("block/fan_grille", seed=101)
    t.fill(0, 0, 16, 16, ALLOY)
    t.bevel(0, 0, 16, 16, 1.15, 0.75)
    for y in range(2, 14):
        for x in range(2, 14):
            t.set(x, y, (0, 0, 0, 0))
    for i in range(2, 14, 3):
        for j in range(2, 14):
            t.set(i, j, ALLOY_DARK[0])
            t.set(j, i, ALLOY_DARK[0])
    grille = t.save()
    b = Tex("block/fan_blade", seed=102)
    b.fill(0, 0, 16, 16, IRON)
    b.bevel(0, 0, 16, 16, 1.05, 0.85)
    return grille, b.save()


def tex_water_wheel():
    t = Tex("block/water_wheel_paddle", seed=111)
    t.planks(0, 0, 16, 16, WOOD, SPRUCE_DARK, board=4, vertical=True)
    p = t.save()
    r = Tex("block/water_wheel_rim", seed=112)
    r.fill(0, 0, 16, 16, SPRUCE)
    for x in range(0, 16, 4):
        for y in range(16):
            r.set(x, y, SPRUCE_DARK[0])
    return p, r.save()


def tex_depot():
    t = Tex("block/depot_top", seed=121)
    t.fill(0, 0, 16, 16, ALLOY)
    t.frame(0, 0, 16, 16, ALLOY_DARK[0])
    t.fill(2, 2, 14, 14, [hexc("5d5d58"), hexc("55554f"), hexc("63635d")])
    t.frame(2, 2, 14, 14, shade(ALLOY[0], 0.75))
    top = t.save()
    s = Tex("block/depot_side", seed=122)
    s.fill(0, 0, 16, 16, ALLOY)
    s.bevel(0, 0, 16, 16)
    for x in range(16):
        s.set(x, 3, ALLOY_DARK[0])
    return top, s.save()


def tex_gauge():
    t = Tex("block/gauge_dial", seed=131)
    t.solid(0, 0, 16, 16, (0, 0, 0, 0))
    t.disc(8, 8, 6.5, [hexc("ece3cc"), hexc("e4dbc2")], ring=[hexc("6b4614")])
    for a in range(-135, 136, 45):
        x = 8 + round(5 * math.sin(math.radians(a)))
        y = 8 - round(5 * math.cos(math.radians(a)))
        t.set(x, y, hexc("3a3a3a"))
    dial = t.save()
    n = Tex("block/gauge_needle", seed=132)
    n.fill(0, 0, 16, 16, [hexc("c42d2d"), hexc("b32626")])
    needle = n.save()
    s = Tex("block/stress_dial", seed=133)
    s.solid(0, 0, 16, 16, (0, 0, 0, 0))
    s.disc(8, 8, 6.5, [hexc("ece3cc"), hexc("e4dbc2")], ring=[hexc("6b4614")])
    for a in range(-135, 136, 9):
        x = 8 + round(5 * math.sin(math.radians(a)))
        y = 8 - round(5 * math.cos(math.radians(a)))
        col = hexc("3fae4a") if a < 0 else (hexc("e0b030") if a < 90 else hexc("c42d2d"))
        s.set(x, y, col)
    return dial, needle, s.save()


def tex_drill():
    t = Tex("block/drill_head", seed=141)
    t.fill(0, 0, 16, 16, IRON)
    for y in range(16):
        x = (y * 2) % 16
        t.set(x, y, IRON_DARK[0])
        t.set((x + 1) % 16, y, IRON_DARK[1])
    return t.save()


def tex_belt():
    t = Tex("block/belt", seed=151)
    t.fill(0, 0, 16, 16, RUBBER)
    for y in range(0, 16, 4):
        for x in range(1, 15):
            t.set(x, y, shade(t.get(x, y), 1.35))
    t.frame(0, 0, 16, 16, hexc("252528"))
    return t.save()


# ---------------------------------------------------------------- item textures


def item_tex(name, painter):
    t = Tex(f"item/{name}", seed=hash(name) & 0xFFF)
    painter(t)
    return flat_item_model(name, t.save())


def sheet(pal, dark):
    def paint(t: Tex):
        for y in range(3, 13):
            for x in range(2 + (12 - y) // 4, 14 - (y - 3) // 4):
                t.set(x, y, t.rng.choice(pal))
        for x in range(2, 14):
            t.set(x, 12, dark)
        for y in range(3, 13):
            t.set(2 + (12 - y) // 4, y, shade(pal[0], 1.15))
    return paint


def pile(pal):
    def paint(t: Tex):
        for y in range(4, 14):
            w = min(y - 3, 13 - y + 4)
            for x in range(8 - w // 1 // 2 - 2, 8 + w // 2 + 2):
                if t.rng.random() < 0.92:
                    t.set(x, y, t.rng.choice(pal))
    return paint


def chunks(pal, ore):
    def paint(t: Tex):
        for (cx, cy, r) in ((5, 6, 3), (10, 9, 3.4), (6, 11, 2.5)):
            t.disc(cx, cy, r, pal, ring=[shade(pal[0], 0.7)])
        for _ in range(7):
            t.set(t.rng.randrange(3, 13), t.rng.randrange(4, 13), t.rng.choice(ore))
    return paint


def tex_wrench(t: Tex):
    for i in range(3, 13):
        t.set(i, 15 - i, BRASS[0])
        t.set(i + 1, 15 - i, BRASS_DARK[0])
    for (x, y) in ((10, 2), (11, 2), (13, 4), (13, 5), (12, 3), (10, 3), (12, 5)):
        t.set(x, y, IRON[0])
    t.set(11, 4, IRON_DARK[0])
    t.disc(4, 12, 1.7, SPRUCE)


def tex_goggles(t: Tex):
    for x in range(1, 15):
        t.set(x, 8, hexc("4a3420"))
    for cx in (5, 11):
        t.disc(cx, 8, 3.2, BRASS, ring=[BRASS_DARK[0]])
        t.disc(cx, 8, 1.8, [hexc("8fd4e8"), hexc("a5e2f2")])


# ================================================================ parts


def shaft_parts(side, end):
    tf = {"up": "#end", "down": "#end"}
    m = Model("shaft", {"side": side, "end": end, "particle": side}, tinted=True)
    m.box((5, 0, 5), (11, 16, 11), "#side", tex_faces=tf)
    PARTS["shaft"] = m.write()
    h = Model("half_shaft", {"side": side, "end": end, "particle": side}, tinted=True)
    h.box((5, 0, 5), (11, 8, 11), "#side", tex_faces=tf)   # the lower half: y 0..8
    PARTS["half_shaft"] = h.write()
    # an icon: the shaft standing up
    i = Model("shaft", {"side": side, "end": end, "particle": side})
    i.box((5, 0, 5), (11, 16, 11), "#side", tex_faces=tf)
    i.display = BLOCK_DISPLAY
    ICONS["shaft"] = i.write("icon")


def cog_teeth(m: Model, count: int, r0: float, r1: float, half_w: float, y0: float, y1: float):
    step = 360 / count
    for k in range(count):
        m.spoke(k * step, r0, r1, half_w, y0, y1, "#side", tex_faces={"up": "#face", "down": "#face"})


def octagon(m: Model, r: float, y0: float, y1: float):
    """A round-ish disc of radius r: two crossed squares (one turned 45)."""
    tf = {"up": "#face", "down": "#face"}
    m.box((8 - r, y0, 8 - r * 0.42), (8 + r, y1, 8 + r * 0.42), "#side", tex_faces=tf)
    m.box((8 - r * 0.42, y0, 8 - r), (8 + r * 0.42, y1, 8 + r), "#side", tex_faces=tf)
    m.box((8 - r, y0, 8 - r * 0.42), (8 + r, y1, 8 + r * 0.42), "#side", tex_faces=tf, rot=("y", 45, (8, 8, 8)))
    m.box((8 - r * 0.42, y0, 8 - r), (8 + r * 0.42, y1, 8 + r), "#side", tex_faces=tf, rot=("y", 45, (8, 8, 8)))


def cog_parts(face, side, hub, shaft_side, shaft_end):
    tx = {"face": face, "side": side, "hub": hub, "shaft": shaft_side, "end": shaft_end, "particle": face}
    for tinted, sub in ((True, "part"), (False, "icon")):
        # small cogwheel: 8 teeth, Create's shape is 2..14 wide, 6..10 tall
        m = Model("cogwheel", tx, tinted=tinted)
        # pitch radius 7.5 px: two small cogs 16 px apart and a small one
        # 22.6 px from a large one (pitch 15) both roll without sliding
        octagon(m, 6.2, 6.5, 9.5)
        cog_teeth(m, 8, 5.5, 8.6, 1.2, 6.5, 9.5)
        m.box((6, 6, 6), (10, 10, 10), "#hub")
        m.box((5, 0, 5), (11, 16, 11), "#shaft", tex_faces={"up": "#end", "down": "#end"})
        if sub == "icon":
            m.display = BLOCK_DISPLAY
            ICONS["cogwheel"] = m.write("icon")
        else:
            PARTS["cogwheel"] = m.write()
        # large cogwheel: 16 teeth, about 2.6 blocks across; the shaft is its
        # own part (it lines up with neighbouring shafts, not with the teeth)
        g = Model("large_cogwheel", tx, tinted=tinted)
        octagon(g, 13.8, 6.5, 9.5)
        cog_teeth(g, 16, 13.0, 16.8, 1.2, 6.5, 9.5)
        # spokes and hub
        for k in range(4):
            g.spoke(k * 90 + 45, 3, 13, 1.4, 6, 10, "#hub")
        g.box((5.5, 5.5, 5.5), (10.5, 10.5, 10.5), "#hub")
        if sub == "icon":
            g.box((5, 0, 5), (11, 16, 11), "#shaft", tex_faces={"up": "#end", "down": "#end"})
            g.display = scaled_display(0.55)
            ICONS["large_cogwheel"] = g.write("icon")
        else:
            PARTS["large_cogwheel"] = g.write()


def casing_parts(casing, port, inner, brass, brass_port):
    """Static full-block casings. Faces with a port are where shafts come out:
    the model's ports face +-x and +-z (a gearbox turned upright), or +-y."""
    tx = {"casing": casing, "port": port, "inner": inner, "particle": casing}
    # gearbox: ports on the four sides (x and z), plain top and bottom (its axis: y)
    g = Model("gearbox", tx)
    g.box((0, 0, 0), (16, 16, 16), "#port", tex_faces={"up": "#casing", "down": "#casing"})
    PARTS["gearbox"] = g.write()
    gi = Model("gearbox", tx)
    gi.box((0, 0, 0), (16, 16, 16), "#port", tex_faces={"up": "#casing", "down": "#casing"})
    gi.display = BLOCK_DISPLAY
    ICONS["gearbox"] = gi.write("icon")
    # a casing with ports top and bottom (encased shaft, clutch, gearshift): axis y
    for name, t, p in (("encased_shaft", casing, port), ("clutch", brass, brass_port), ("gearshift", brass, brass_port)):
        e = Model(name, {"casing": t, "port": p, "particle": t})
        e.box((0, 0, 0), (16, 16, 16), "#casing", tex_faces={"up": "#port", "down": "#port"})
        PARTS[name] = e.write()
        ei = Model(name, {"casing": t, "port": p, "particle": t})
        ei.box((0, 0, 0), (16, 16, 16), "#casing", tex_faces={"up": "#port", "down": "#port"})
        ei.display = BLOCK_DISPLAY
        ICONS[name] = ei.write("icon")


def crank_parts(handle, grip, alloy_end, shaft_side):
    """Hand crank: its base sits on the block face it is placed against (model
    facing up: base at y 0, handle turning about y). All of it turns."""
    tx = {"handle": handle, "grip": grip, "base": alloy_end, "shaft": shaft_side, "particle": handle}
    for tinted, sub in ((True, "part"), (False, "icon")):
        m = Model("hand_crank", tx, tinted=tinted)
        m.box((5, 0, 5), (11, 6, 11), "#shaft", tex_faces={"up": "#base", "down": "#base"})
        m.box((1, 4, 6.5), (15, 7, 9.5), "#handle")          # the arm
        m.box((6.5, 4, 1), (9.5, 7, 15), "#handle")          # cross arm
        m.box((12, 7, 6.5), (15, 13, 9.5), "#grip")         # the grip
        m.box((6, 3, 6), (10, 8, 10), "#base")
        if sub == "icon":
            m.display = BLOCK_DISPLAY
            ICONS["hand_crank"] = m.write("icon")
        else:
            PARTS["hand_crank"] = m.write()


def motor_parts(body, cap):
    """Creative motor, facing up: its shaft comes out of the top."""
    tx = {"body": body, "cap": cap, "particle": body}
    for sub in ("part", "icon"):
        m = Model("creative_motor", tx)
        m.box((3, 0, 3), (13, 12, 13), "#body", tex_faces={"up": "#cap", "down": "#cap"})
        m.box((2, 9, 2), (14, 14, 14), "#cap")
        m.box((1, 0, 1), (15, 2, 15), "#cap")
        if sub == "icon":
            m.display = BLOCK_DISPLAY
            ICONS["creative_motor"] = m.write("icon")
        else:
            PARTS["creative_motor"] = m.write()


def press_parts(casing, port, inner, head):
    """Mechanical press: a casing open at the bottom middle (Create's 4..12
    hole), its shaft along x, and the head that comes down below it."""
    tx = {"casing": casing, "port": port, "inner": inner, "head": head, "particle": casing}
    for sub in ("part", "icon"):
        m = Model("press", tx)
        # four walls round the 4..12 shaft of the head
        m.box((0, 2, 0), (16, 16, 4), "#casing", tex_faces={"east": "#port", "west": "#port"})
        m.box((0, 2, 12), (16, 16, 16), "#casing", tex_faces={"east": "#port", "west": "#port"})
        m.box((0, 2, 4), (4, 16, 12), "#casing", tex_faces={"west": "#port"})
        m.box((12, 2, 4), (16, 16, 12), "#casing", tex_faces={"east": "#port"})
        m.box((4, 14, 4), (12, 16, 12), "#inner")
        if sub == "icon":
            m.box((4, -2, 4), (12, 2, 12), "#head")
            m.display = BLOCK_DISPLAY
            ICONS["mechanical_press"] = m.write("icon")
        else:
            PARTS["press"] = m.write()
    # the head: a plate and a pole; the plot raises it 4 px to rest inside
    # the casing and lowers it onto the depot or the ground below
    h = Model("press_head", tx)
    h.box((5, 4, 5), (11, 12, 11), "#head")
    h.box((3, 0, 3), (13, 4, 13), "#head")
    PARTS["press_head"] = h.write()


def millstone_parts(side, top, cog_face, cog_side, hub):
    tx = {"side": side, "top": top, "face": cog_face, "cside": cog_side, "hub": hub, "particle": side}
    b = Model("millstone_base", tx)
    b.box((0, 0, 0), (16, 6, 16), "#side", tex_faces={"up": "#top", "down": "#top"})
    PARTS["millstone_base"] = b.write()
    for tinted, sub in ((True, "part"), (False, "icon")):
        # the top stone turns, with a small cogwheel ring round its foot
        m = Model("millstone", tx, tinted=tinted)
        m.box((2, 9, 2), (14, 16, 14), "#side", tex_faces={"up": "#top", "down": "#top"})
        for k in range(8):
            m.spoke(k * 45, 5, 8.6, 1.2, 6, 9, "#cside", tex_faces={"up": "#face", "down": "#face"})
        m.box((3, 6, 3), (13, 9, 13), "#cside", tex_faces={"up": "#face", "down": "#face"})
        if sub == "icon":
            m.box((0, 0, 0), (16, 6, 16), "#side", tex_faces={"up": "#top", "down": "#top"})
            m.display = BLOCK_DISPLAY
            ICONS["millstone"] = m.write("icon")
        else:
            PARTS["millstone"] = m.write()


def fan_parts(casing, port, grille, blade):
    """Encased fan, facing up (+y): the grille on top, the shaft port below."""
    tx = {"casing": casing, "port": port, "grille": grille, "particle": casing}
    for sub in ("part", "icon"):
        m = Model("encased_fan", tx)
        m.box((0, 0, 0), (16, 16, 16), "#casing", faces=("north", "south", "east", "west"))
        m.box((0, 0, 0), (16, 2, 16), "#port", faces=("down", "up"))
        m.box((0, 15, 0), (16, 16, 16), "#grille", faces=("up", "down"))
        if sub == "icon":
            m.display = BLOCK_DISPLAY
            ICONS["encased_fan"] = m.write("icon")
        else:
            PARTS["encased_fan"] = m.write()
    p = Model("fan_propeller", {"blade": blade, "particle": blade}, tinted=True)
    p.box((6.5, 4, 6.5), (9.5, 12, 9.5), "#blade")
    for k in range(4):
        # blades tipped 22.5 degrees like a propeller
        a = k * 90
        p.spoke(a, 1.5, 7, 2.2, 9, 10, "#blade")
    PARTS["fan_propeller"] = p.write()


def water_wheel_parts(paddle, rim, hub, shaft_side, shaft_end):
    tx = {"paddle": paddle, "rim": rim, "hub": hub, "shaft": shaft_side, "end": shaft_end, "particle": paddle}
    for size, name, rr, pw in ((1, "water_wheel", 14.5, 3.2), (2, "large_water_wheel", 23.0, 4.5)):
        for tinted, sub in ((True, "part"), (False, "icon")):
            m = Model(name, tx, tinted=tinted)
            # paddles round the y axis, two rims and spokes
            for k in range(8):
                m.spoke(k * 45, rr - 5.5, rr, 0.8, 1, 15, "#paddle")
                m.spoke(k * 45 + 22.5, 2.5, rr - 4, 0.9, 2, 4, "#rim")
                m.spoke(k * 45 + 22.5, 2.5, rr - 4, 0.9, 12, 14, "#rim")
            for k in range(16):
                m.spoke(k * 22.5, rr - 5.5, rr - 4, rr * 0.2, 2, 4, "#rim")
                m.spoke(k * 22.5, rr - 5.5, rr - 4, rr * 0.2, 12, 14, "#rim")
            m.box((5, 1, 5), (11, 15, 11), "#hub")
            if sub == "icon":
                m.box((5, 0, 5), (11, 16, 11), "#shaft", tex_faces={"up": "#end", "down": "#end"})
                m.display = scaled_display(0.5 if size == 1 else 0.36)
                ICONS[name] = m.write("icon")
            else:
                PARTS[name] = m.write()


def depot_parts(top, side):
    tx = {"top": top, "side": side, "particle": side}
    for sub in ("part", "icon"):
        m = Model("depot", tx)
        m.box((0, 0, 0), (16, 13, 16), "#side", tex_faces={"up": "#top", "down": "#top"})
        if sub == "icon":
            m.display = BLOCK_DISPLAY
            ICONS["depot"] = m.write("icon")
        else:
            PARTS["depot"] = m.write()


def gauge_parts(casing, port, dial, needle, stress_dial):
    """Gauges: a casing through which a shaft runs along y, with dials on the
    four sides; the needle is its own part (turned by the plot)."""
    for name, d in (("speedometer", dial), ("stressometer", stress_dial)):
        tx = {"casing": casing, "port": port, "dial": d, "particle": casing}
        for sub in ("part", "icon"):
            m = Model(name, tx)
            m.box((2, 0, 2), (14, 16, 14), "#casing", tex_faces={"up": "#port", "down": "#port"})
            m.box((1, 1, 1.5), (15, 15, 1.5), "#dial", faces=("north",))
            m.box((1, 1, 14.5), (15, 15, 14.5), "#dial", faces=("south",))
            m.box((1.5, 1, 1), (1.5, 15, 15), "#dial", faces=("west",))
            m.box((14.5, 1, 1), (14.5, 15, 15), "#dial", faces=("east",))
            if sub == "icon":
                m.display = BLOCK_DISPLAY
                ICONS[name] = m.write("icon")
            else:
                PARTS[name] = m.write()
    n = Model("gauge_needle", {"needle": needle, "particle": needle})
    # pointing up on the north face; turned about z by the plot
    n.box((7.5, 7.5, 1.0), (8.5, 13.5, 1.4), "#needle")
    n.box((7, 7, 0.9), (9, 9, 1.4), "#needle")
    PARTS["gauge_needle"] = n.write()


def drill_parts(casing, port, head):
    """Mechanical drill facing up: a casing below, the drill head above it."""
    tx = {"casing": casing, "port": port, "head": head, "particle": casing}
    for sub in ("part", "icon"):
        m = Model("drill", tx)
        m.box((0, 0, 0), (16, 10, 16), "#casing", tex_faces={"down": "#port"})
        if sub == "icon":
            for (r, y0, y1) in ((6, 10, 12), (4.5, 12, 14), (3, 14, 15.5), (1.5, 15.5, 16)):
                m.box((8 - r, y0, 8 - r), (8 + r, y1, 8 + r), "#head")
            m.display = BLOCK_DISPLAY
            ICONS["mechanical_drill"] = m.write("icon")
        else:
            PARTS["drill"] = m.write()
    h = Model("drill_head", {"head": head, "particle": head}, tinted=True)
    for (r, y0, y1) in ((6, 10, 12), (4.5, 12, 14), (3, 14, 15.5), (1.5, 15.5, 17)):
        h.box((8 - r, y0, 8 - r), (8 + r, y1, 8 + r), "#head")
        h.box((8 - r, y0, 8 - r), (8 + r, y1, 8 + r), "#head", rot=("y", 45, (8, 8, 8)))
    h.box((5, 0, 5), (11, 10, 11), "#head")
    PARTS["drill_head"] = h.write()


def items():
    flat = {
        "wrench": tex_wrench,
        "goggles": tex_goggles,
        "iron_sheet": sheet(IRON, IRON_DARK[0]),
        "golden_sheet": sheet([hexc("f2d14b"), hexc("e8c23c"), hexc("f7dc6a")], hexc("b8901f")),
        "copper_sheet": sheet(COPPER, hexc("8a4428")),
        "brass_sheet": sheet(BRASS, BRASS_DARK[0]),
        "wheat_flour": pile([hexc("eee6cf"), hexc("e3d9bd"), hexc("f6f0de")]),
        "cinder_flour": pile([hexc("8a3b37"), hexc("7a312e"), hexc("9c4642")]),
        "dough": pile([hexc("e9cf9a"), hexc("dfc189"), hexc("f1daa8")]),
        "andesite_alloy": sheet(ALLOY, ALLOY_DARK[0]),
        "crushed_raw_iron": chunks(STONE, [hexc("d8af93")]),
        "crushed_raw_gold": chunks(STONE, [hexc("fcee4b")]),
        "crushed_raw_copper": chunks(STONE, [hexc("e0734a")]),
        "zinc_nugget": pile([hexc("a8c0b4"), hexc("9ab3a7")]),
    }
    for name, painter in flat.items():
        model = item_tex(name, painter)
        ICONS[name] = model


# ================================================================ main


def main():
    shaft_side, shaft_end = tex_shaft()
    casing, port, inner = tex_casing()
    brass, brass_port = tex_brass_casing()
    cog_face, cog_side, hub = tex_cog()
    handle, grip = tex_crank()
    iron, iron_dark = tex_iron()
    head = tex_press()
    motor_body, motor_cap = tex_motor()
    mill_side, mill_top = tex_millstone()
    grille, blade = tex_fan()
    paddle, rim = tex_water_wheel()
    depot_top, depot_side = tex_depot()
    dial, needle, stress_dial = tex_gauge()
    drill_head = tex_drill()
    tex_belt()

    shaft_parts(shaft_side, shaft_end)
    cog_parts(cog_face, cog_side, hub, shaft_side, shaft_end)
    casing_parts(casing, port, inner, brass, brass_port)
    crank_parts(handle, grip, shaft_end, shaft_side)
    motor_parts(motor_body, motor_cap)
    press_parts(casing, port, inner, head)
    millstone_parts(mill_side, mill_top, cog_face, cog_side, hub)
    fan_parts(casing, port, grille, blade)
    water_wheel_parts(paddle, rim, hub, shaft_side, shaft_end)
    depot_parts(depot_top, depot_side)
    gauge_parts(brass, brass_port, dial, needle, stress_dial)
    drill_parts(casing, port, drill_head)
    items()

    spinning = {"shaft", "half_shaft", "cogwheel", "large_cogwheel", "hand_crank", "millstone",
                "fan_propeller", "water_wheel", "large_water_wheel", "drill_head"}
    for name, model in PARTS.items():
        item_def(f"part/{name}", model, tinted=name in spinning)
    for name, model in ICONS.items():
        item_def(name, model)
    listing = {"parts": sorted(PARTS), "spinning": sorted(spinning), "items": sorted(ICONS)}
    (ASSETS.parent / "src" / "parts.json").write_text(json.dumps(listing, indent=1) + "\n")
    print(f"{len(PARTS)} parts, {len(ICONS)} items")


if __name__ == "__main__":
    main()
