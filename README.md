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
Environment sky/fog, shadow settings, author labels and preview scripts are not
exported; visual parity with the editor is **not** claimed. Tangent/normal-map
quality, foliage transparency and mesh-chunk draw-call cost need rendered review.

The production-loader fixture copies the chosen Comunicare world services into a
disposable project with isolated HOME/XDG data. It checks the actual archive,
client menu button actions, shared state, storage reopening and script stop cleanup.
Current result: **2,293 checks pass** (mostly per-node no-script checks), not 2,293
independent gameplay scenarios. It is not a full application/headset test: actual
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

- 300 × 270 m bounded landscape, broad playable meadow, stream/bridge and trails.
- 18 named areas, 21 connected authored routes, western and eastern exploration loops.
- Farm/village ruins, woodland/watchtower, chapel refuge and a roofed crypt wing
  with galleries, ossuary, armory, antechamber and guardian hall.
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

Uses an isolated project/HOME/XDG copy under `/tmp/opencode`, imports assets,
runs real Godot collision queries, progression/storage rules, actual station button
actions and the desktop preview smoke test. Set
`GODOT=/path/to/godot` if necessary. Current result: **320 map + 41 progression +
56 menu assertions, zero failures**;
**28 asset-file SHA-256 hashes verified**. Return codes: 0 pass, 1 assertion failure,
2 infrastructure/engine errors. No real account, relay, microphone or XR is used.
Route tests check centerline obstructions and sampled ground, not full capsule
clearance, navigation-agent behavior or accessibility at all possible positions.

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

This is a first map implementation, **not final high-quality art sign-off**.
The detailed scanned nature assets/PBR materials are present, but buildings are
original modular masonry shells; the meadow uses a grass surface, not yet dense
blade vegetation or sculpted terrain. Trees/rocks are decorative without individual
collision. Labels are authoring wayfinding rather than final in-world signage.

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
