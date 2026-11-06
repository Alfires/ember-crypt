# Ember Crypt — Ashen Vale

Godot **4.7** authoring repository for a **Comunicare world only**, not a standalone
game. A script-free exploration package now exports and passes tests against the
updated Comunicare safe loader/runtime. The complete roguelike is not finished.

## Build and open in Comunicare

```sh
python3 tools/package_world.py
python3 tests/run_package.py --comunicare /path/to/comunicare
```

In Comunicare, choose **World Explorer → Open local map…** and select
`build/ember-crypt.cworld`. Use Comunicare's own player and desktop/VR interaction
controls near a lectern. The archive contains **no GDScript, preview player,
project.godot, GLTF binaries or import caches**. Do not ZIP the authoring repository
as a substitute. The output is ignored by Git and rebuilt locally.

The supported package slice includes the full static map/scanned model conversion,
spawn, four station menus, creator Credits/license text, shared run-state notes and
a saved map-note action through **Comunicare's player/world-scoped storage.local**.
It does not yet port author-preview exploration XP/upgrade logic. Menu pages label
unfinished gameplay honestly rather than claiming their descriptions implement it.
Opening a page never awards XP. Save-note success is verified by integration tests;
the current package UI does not yet show detailed write failure/retry status.

Export flattens source instances and converts texture maps to PNG and static
geometry to bounded `.worldmesh` chunks. Triplanar projection is baked into UVs.
Dense scans use author-side engine LOD reduction, then triangle partitioning to
fit parser fuel limits. No client validators or sibling files are modified.
Environment fog, shadow settings, author labels and preview scripts are not
exported; a reviewed static sky dome replaces the unsupported environment sky.
Visual parity with the editor is **not** claimed. Tangent/normal-map
quality, foliage transparency and mesh-chunk draw-call cost need rendered review.

The production-loader fixture copies the chosen Comunicare world services into a
disposable project with isolated HOME/XDG data. It checks the actual archive,
client menu button actions, shared state, storage reopening and script stop cleanup.
Current result: **3,846 checks pass** (mostly per-node no-script checks), not 3,846
independent gameplay scenarios. Includes exported route clearance, twelve rigid
pickup bodies and settling physics, foliage cutout settings and geometry sharing.
All 29 routes also undergo a swept 0.35 m-radius, 1.8 m-high capsule check. This
found a shrine lectern and supply case encroaching on routes; deterministic
route-aware prop placement now keeps them clear. Capsule sweeps use a lifted
horizontal segment; they are not a complete walking/step-climbing simulation.
It is not a full application/headset test: actual
player input targeting, DataLoader transitions and client UI navigation remain
manual/integration gates. No relay, real account, microphone or headset is started.
The code must include `ui.local`, `state.local`, `world_menu.gd` and UI schema
support; the older primitive-only client is incompatible despite both reporting
world API 1. The installed client must reject unsupported capabilities.

Local Comunicare packages currently scope saves by package revision; repacking
can select a new save namespace. Published source identity/migration still needs
a deliberate policy before progression persistence across world updates is promised.

## Author-only local preview (not the delivery target)

Open `project.godot` in Godot and press F6 on `scenes/world.tscn`, or F5 to run.
Command line: `godot --path /path/to/ember-crypt`.

WASD moves, Shift runs, mouse looks, E opens a nearby station, Esc releases the
mouse/closes a panel. Four working progression/map panels sit at camp, shrine,
chapel and crypt entry; the Credits lectern immediately beside camp spawn shows
the actual asset creators. Panels stop preview movement and work offline.

Discover landmarks to earn **25 one-time exploration XP** each. Every 100 run XP
grants a choice of damage, cooldown or health upgrade. All four stations share ten
menu pages: Overview, Stats, Upgrades, Level up, Build, Milestones, Cosmetics, XP,
Map and Save data. Opening menus awards no XP. These are exploration rewards,
not pretend combat victories; enemy rewards will come with actual combat.

Lifetime XP, discoveries and amber/teal cosmetic selection persist in
`user://ember-crypt-progress.json`. The selected cosmetic is a saved preference;
spell visuals are not implemented. Camp offers a new exploration run and a
two-step confirmed progression reset. New runs clear temporary upgrades, not
discoveries: revisiting landmarks cannot farm lifetime XP. Consequently this first
exploration track is finite, not yet the repeatable combat leveling loop.
Malformed, oversized and future-version saves are preserved with temporary play
and an explicit error; write failures remain visibly unsaved and can be retried.
The standalone save is not account-scoped or the Comunicare storage API.

## Built map

- **440 × 370 m** landscape, broad playable meadow, stream/bridge and aligned trails.
- **22 named areas, 29 connected routes**, including North pass, Old quarry,
  Eastern grove and Southern copse; western/eastern exploration loops.
- **115 tree placements and 75 scanned rock clusters**, rounded horizon foothills,
  camp/ruin tables, benches and route-safe supply crates. Safe export selects one
  scanned tree variant per placement rather than importing the full catalogue.
  Safe export now adds 190 static collision bodies, derived from the selected
  tree's trunk surface and each rock's visual bounds. Foliage does not collide.
  These are axis-aligned primitive approximations, not exact mesh collision;
  irregular rock contours may have conservative blocking margins. The production
  package suite ray-tests each body and rechecks all 29 capsule route sweeps.
- **18,470 bent grass blades in 55 irregular static patches**, with varied height,
  lean and orientation. Placement excludes route verges, buildings, water and
  interaction clearings. Original generated geometry is under `assets/vegetation/`
  and credited in the world menu; no third-party grass license is implied.
  Geometry is static: no wind shader, animation or collision. This is an initial
  grass pass, not photorealistic vegetation or full terrain art completion.
- Three original low rolling earth banks break up the meadow floor; grass follows
  their height. Dark forest-floor verges soften road borders. `tools/terrain.py`
  generates the banks with bounded slopes, preserving flat travel centerlines.
  Collision uses 3 m box cells (not a smooth triangle-mesh collider), so small
  height discrepancies/steps remain an explicit client movement-validation gate.
- **12 pickup supply cases** distributed through camp, ruins and crypt. They export
  as real RigidBody3Ds with attached geometry/collision for Comunicare carrying;
  they do not grant healing, inventory items or XP. Actual client grip testing is
  still required; isolated tests verify export structure and real settling physics.
- Farm/village ruins, woodland/watchtower, chapel refuge and a roofed crypt wing
  with galleries, ossuary, armory, antechamber and guardian hall.
- Landmarks now include original timber roof framing, damaged plank roofs,
  masonry courses, doorway trim, chapel/crypt buttresses and interior ceiling ribs.
  Route-clearance checks omit details that would block travel. These are authored
  architectural improvements, not an imported finished environment pack.
- Original composition using detailed CC0 scanned Poly Haven trees/boulders and
  PBR surface textures, not a low-poly purchased environment/demo pack.
- Ordinary editable static TSCN geometry/collision: no map-generation script runs
  during play. `tools/build_map.py` reproducibly rebuilds the checked-in scene.

```text
                      NORTH
 Watchtower ----- Village ------ Chapel [L]
     |                |              |
 Woodland          Bridge ------- Forecourt
     |                |              |
 Shrine [L] ------- FIELD         Crypt entry [L]
     |              / |              |
 Farm -------- South road         Galleries
                    |             /       \
                Camp [S C L]   Ossuary -- Armory
                                  \       /
                                  Antechamber
                                       |
                                  Guardian hall
```

`L`: physical map/leveling-info menu; `S`: spawn; `C`: asset creator Credits.
The field/ford route also branches east. `map.json` is the exact authoritative
area/route graph; this diagram is schematic.

## Verify

```sh
python3 tests/run.py
```

Uses an isolated project/HOME/XDG copy under ignored `build/test-tmp/`, imports assets,
runs real Godot collision queries, progression/storage rules, actual station button
actions and the desktop preview smoke test. Set
`GODOT=/path/to/godot` if necessary. Current result: **429 map + 41 progression +
56 menu assertions and five Python landscape tests, zero failures**;
**28 asset-file SHA-256 hashes verified**. Return codes: 0 pass, 1 assertion failure,
2 infrastructure/engine errors. No real account, relay, microphone or XR is used.
Author-map tests check centerline obstructions and sampled ground; the separate
package suite additionally sweeps player-width capsules. Neither verifies actual
navigation agents, step climbing or accessibility at all possible positions.

Regenerate: `python3 tools/build_map.py`. Selected source assets were imported
from the existing local Comunicare asset inventory using:

```sh
python3 tools/import_assets.py /path/to/comunicare
```

All copied source files were checked against its recorded hashes before import.
There are no runtime dependencies on that checkout. Asset authors, original URLs,
download URLs and per-file hashes are in `assets/provenance.json`; license text
is in `assets/licenses/CC0-1.0.txt`. CC0 applies to those assets, not automatically
to original project code. No repository-wide code license has been selected.

## Explicit unfinished work

For real rendered package review (requires an available graphical display):

```sh
python3 tests/run_package.py --comunicare /path/to/comunicare --render
# Smaller review run:
python3 tests/run_package.py --comunicare /path/to/comunicare --render --view chapel
```

Captures grass close-up, camp, field, woodland and overview under `build/review/` using the actual
safe loader. A Compatibility/Intel UHD 630 capture completed; the graphics stack
also printed NVIDIA driver-selection warnings. This is not a performance or
headset certification. A denser experimental foliage configuration timed out and
was replaced with the lower-geometry tested configuration. The current grass export uses
158 meshes, 117,465 vertices and 246,684 indices; repeated instances
still incur rendering cost. No final-quality art approval is implied by screenshots.
Latest nature-collision pass: 3,846 package checks pass after route-safe prop placement.
An earlier package-test attempt and a full rendered capture timed out; individual
chapel and crypt-interior capture runs subsequently completed. Chapel review still
shows simple walls, flat surrounding ground and sparse tree silhouettes: capture
completion is not final art approval. Graphics driver-selection warnings persist.
Temporary projects now use ignored `build/test-tmp/` because shared `/tmp` filled;
no unrelated temporary files were removed. This also applies to package export.

This is a first map implementation, **not final high-quality art sign-off**.
The detailed scanned nature assets/PBR materials are present, but buildings are
original modular masonry shells; the meadow now has blade patches but still needs
more convincing ground variation and sculpted terrain. Trees/rocks now have
primitive collision in the safe export; author preview collision is not yet
equivalent. Labels are authoring wayfinding rather than final in-world signage.

The crypt is currently roofed at surface level, not excavated below terrain.
Enemy AI/combat, guardian, objective gates, seeded encounters, healing, combat XP,
animations and shortcuts are **not implemented**. Author-only exploration XP,
local progression and run upgrade selection work in the local tooling, not yet in
the Comunicare package; calculated stats do not affect combat. Package menus use
client-provided VR presentation, but headset input remains unverified. No
20–30 minute gameplay claim. Menus have headless behavioral tests, but rendered
layout/accessibility and physical headset input remain manual gates.

The author-side desktop preview uses trusted local GDScript. Do **not** upload this
repository as a playable safe ZIP, disable validators or execute these scripts in
downloaded worlds. Use the explicit conversion above. Further gameplay must be
implemented with the supported reviewed world APIs. Neither headless checks nor the Compatibility renderer validate final
Forward Plus visuals, headset performance or comfort. Rendered art review remains open.

Remote: https://github.com/Alfires/ember-crypt (`main` tracks `origin/main`).
Do not add caches, user saves or credentials.
