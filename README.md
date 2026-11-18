# tc-create

Create-style kinetics for a DiamondFire plot, written in
[Terracotta](https://owlfroggy.github.io/terracotta-beta-docs/). Shafts,
cogwheels and gearboxes carry rotation from hand cranks, water wheels and
motors to presses, millstones, fans and drills, with Create's speed ratios
and stress limits. Players can walk and stand on the blocks, even though they
are display entities.

The rules come from Create's source
([Creators-of-Create/Create](https://github.com/Creators-of-Create/Create),
`mc1.21.1/dev`). Create's code is MIT. Its assets (textures, models, sounds)
are All Rights Reserved, so this project does **not** copy them: every texture
and model in `pack/` is drawn from scratch in Create's style by
`pack/src/create_pack.py`.

## How it works

- **Blocks** are item displays (one per part) plus an interaction hitbox for
  clicks. Their records live in `tc/state.tc`, keyed by `"x,y,z"`, and are
  saved across plot restarts.
- **Spinning** is done on the GPU. Each spinning part's model tints every
  face with custom model data color 0. The plot packs the axis, the speed and
  the pivot block into that color (`kineticTint` in `tc/render.tc`). The
  pack's core shader (`pack/assets/minecraft/shaders/core/item.vsh`) unpacks
  it and turns the vertices. It uses Create's angle formula: render ticks ×
  RPM × 0.3°, plus 22.5° on even blocks (11.25° for large cogs). Meshing cogs
  therefore line up as they do in Create. The plot only writes a part again
  when its speed changes.
- **Rotation** (`tc/kinetics.tc`) follows Create's `RotationPropagator`:
  - Shafts connect through faces where both blocks have a shaft end.
  - A gearbox reverses through-rotation. A powered gearshift reverses one side.
  - Two small cogs side by side turn opposite ways (−1).
  - A large cog drives a diagonal small cog at −2×.
  - Two large cogs at right angles connect at ±1.

  The strongest source sets the network's speed. These conflicts break the
  block that caused them, as in Create:
  - two sources turning opposite ways;
  - a loop whose ratios disagree;
  - any block faster than 256 RPM.
- **Stress**: a network's stress is the sum of impact × |speed|. Its capacity
  is the sum of capacity × |generated speed|. Above capacity the whole
  network stops (overstressed). The values per block are Create's.
- **Standing on blocks** (`tc/proxy.tc`): the client cannot collide with
  display entities. So when a player touches a Create block while standing
  on something (or falling onto it), they swap into a proxy:
  - They ride an invisible marker armor stand.
  - Every tick, the plot moves the stand with vanilla walking physics, driven
    by the player's keys and look. It collides with world blocks and with the
    Create blocks' shapes. The physics include acceleration, friction, air
    drag, gravity, jumping, sprinting, sneaking (it holds you on edges) and
    0.6-block step-up.
  - A mannequin with the player's skin walks in their place for others.
  - When the player no longer touches a Create block, they swap back at the
    proxy's spot and keep its velocity.

## Blocks

| Block | Notes |
| --- | --- |
| Shaft, Cogwheel, Large Cogwheel | Cogwheels placed beside a cogwheel take its axis, so they mesh |
| Gearbox | Shafts on its four sides; reverses straight through |
| Clutch, Gearshift | A powered block next to them disengages the clutch or reverses the gearshift |
| Hand Crank | Right click turns it at 32 RPM for half a second (sneak: backwards); 8 su/RPM |
| Creative Motor | Right click steps its speed up (1 … 256 RPM), sneak + right click down; past the end it reverses |
| Water Wheel, Large Water Wheel | Turn at 8 / 4 RPM with the flow of the water around them, as Create scores it |
| Mechanical Press | Presses items on a depot below, or lying on the ground below it (Create's pressing recipes) |
| Millstone | A small cog. Right click to put items in, or throw them on top. Results drop out (Create's milling recipes) |
| Encased Fan | Blows or sucks along its facing, 3 to 20 blocks by speed. Pushes entities and proxy players. Water, lava, fire and soul fire in the current wash, blast, smoke or haunt items |
| Mechanical Drill | Breaks the block in front of it, faster at higher speed |
| Depot | Holds one stack; right click to put or take |
| Speedometer, Stressometer | Needles on four sides; right click for a reading |

Tools: the **wrench** (right click turns a block; sneak + right click picks
it up) and **Engineer's Goggles** (right click to wear). While you wear the
goggles or hold either tool, the block you look at shows its speed, impact or
capacity, and its network's stress, on your action bar.

Create materials made by recipes include iron, golden and copper sheets,
wheat flour, cinder flour, dough and crushed ores. They are paper items with
models from the pack.

## Commands

| Command | What it does |
| --- | --- |
| `@kit` | Every block (16 each), a wrench and goggles |
| `@help` | How to use them |
| `@clearcreate` | Removes every Create block |
| `@reload` | Rebuilds every block's displays from the saved list |
| `@stats` | Block and network count, plot CPU |
| `@pack` | Sends the resource pack again |

## Layout

| Path | Contents |
| --- | --- |
| `tc/` | Plot code: `main.tc` (events, loop, commands), `state.tc`, `util.tc`, `blocks.tc` (types, shapes, parts), `kinetics.tc`, `render.tc`, `registry.tc`, `machines.tc`, `interact.tc`, `proxy.tc`, `items.tc`, `pack.tc`, `recipes_data.tc` (generated) |
| `pack/src/create_pack.py` | Draws every texture and writes every model and item file |
| `pack/assets/minecraft/shaders/core/item.vsh` | The spin shader |
| `tools/build_pack.py` | Validates the pack (JSON, paths, the shader under every 26.3 define set with `glslc`), zips it and publishes it to the `pack-dist` branch |
| `tools/gen_recipes.py` | Writes `tc/recipes_data.tc` from a Create checkout's recipe data |
| `tools/kinetic_check.py` | Checks the spin color round trip and that cogwheels mesh, offline |

## Build and put it on the plot

```bash
python3 pack/src/create_pack.py
python3 tools/build_pack.py --publish --push
```

Then compile `tc/` and send it with the Terracotta VS Code extension (plot
size 300 in `.vscode/launch.json`), or with the `tc-send.py` script. Needs
Minecraft 26.3 (pack format 97.1) and Terracotta 1.0.0-beta.

## Not done yet

- Mechanical belts, funnels, chutes, mixers and basins, saws, deployers,
  steam engines, windmills and contraptions.
- Breaking takes one click (no mining time).
- In third person, a proxy player does not see their own mannequin.
