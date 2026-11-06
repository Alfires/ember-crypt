#!/usr/bin/env python3
"""Generate an ordinary editable TSCN map. Runtime map construction is not needed."""
import json
import math
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]
RNG = random.Random(83742)
AREAS = {
    "camp": [0, 95], "south_road": [0, 70], "field": [0, 30],
    "farm": [-72, 65], "shrine": [-95, 22], "woodland": [-95, -25],
    "watchtower": [-85, -80], "ford": [30, 50], "bridge": [15, -20],
    "village": [0, -75], "chapel": [75, -80], "forecourt": [85, -30],
    "crypt_entry": [105, 8], "galleries": [105, 38], "ossuary": [80, 68],
    "armory": [130, 68], "antechamber": [105, 95], "guardian": [105, 125],
    "north_pass": [-50, -145], "eastern_grove": [175, -65],
    "old_quarry": [-175, -45], "southern_copse": [-85, 165],
}
EDGES = [
    ("camp", "south_road"), ("south_road", "field"), ("south_road", "farm"),
    ("farm", "shrine"), ("shrine", "woodland"), ("woodland", "watchtower"),
    ("shrine", "field"), ("watchtower", "village"), ("field", "ford"),
    ("field", "bridge"), ("bridge", "village"), ("village", "chapel"),
    ("chapel", "forecourt"), ("bridge", "forecourt"), ("forecourt", "crypt_entry"),
    ("crypt_entry", "galleries"), ("galleries", "ossuary"), ("galleries", "armory"),
    ("ossuary", "antechamber"), ("armory", "antechamber"), ("antechamber", "guardian"),
    ("watchtower", "north_pass"), ("north_pass", "village"),
    ("chapel", "eastern_grove"), ("eastern_grove", "forecourt"),
    ("woodland", "old_quarry"), ("old_quarry", "shrine"),
    ("farm", "southern_copse"), ("southern_copse", "camp"),
]
STATIONS = ["camp", "shrine", "chapel", "crypt_entry"]


def distance_to_routes(x, z):
    best = math.inf
    for a, b in EDGES:
        ax, az = AREAS[a]
        bx, bz = AREAS[b]
        vx, vz = bx-ax, bz-az
        t = max(0, min(1, ((x-ax)*vx+(z-az)*vz)/(vx*vx+vz*vz)))
        best = min(best, math.hypot(x-ax-t*vx, z-az-t*vz))
    return best


def safe_offset(ax, az, preferred):
    for dx, dz in [preferred, (6,-6), (-6,-6), (-6,6), (8,3), (-8,3)]:
        if distance_to_routes(ax+dx, az+dz) >= 2.5:
            return ax+dx, az+dz
    raise ValueError("No safe prop location near landmark")


class Scene:
    def __init__(self):
        self.resources = []
        self.nodes = []
        self.counter = 0
        self.shared_resources = {}

    def resource(self, kind, properties):
        signature = (kind, properties)
        if signature in self.shared_resources:
            return self.shared_resources[signature]
        key = f"r{len(self.resources)}"
        self.resources.append(f'[sub_resource type="{kind}" id="{key}"]\n{properties}\n')
        reference = f'SubResource("{key}")'
        self.shared_resources[signature] = reference
        return reference

    def node(self, name, kind, parent=".", properties="", groups=None):
        extra = f' groups={json.dumps(groups)}' if groups else ""
        self.nodes.append(f'[node name="{name}" type="{kind}" parent="{parent}"{extra}]\n{properties}\n')

    def box(self, name, xyz, size, material, collision=True, parent="."):
        self.counter += 1
        name = f"{name}_{self.counter}"
        mesh = self.resource("BoxMesh", f"size = Vector3{tuple(size)}")
        self.node(name, "MeshInstance3D", parent, f"position = Vector3{tuple(xyz)}\nmesh = {mesh}\nmaterial_override = {material}")
        if name.startswith("Boundary"):
            self.nodes[-1] += "visible = false\n"
        if collision:
            shape = self.resource("BoxShape3D", f"size = Vector3{tuple(size)}")
            path = name if parent == "." else parent + "/" + name
            self.node("Body", "StaticBody3D", path)
            self.node("Collision", "CollisionShape3D", path + "/Body", f"shape = {shape}")

    def label(self, text, xyz, size=40):
        self.counter += 1
        self.node(f"Label_{self.counter}", "Label3D", properties=f"position = Vector3{tuple(xyz)}\ntext = {json.dumps(text)}\nfont_size = {size}\npixel_size = 0.012\nbillboard = 1\nmodulate = Color(0.91, 0.83, 0.64, 1)")

    def ellipsoid(self, name, xyz, scale, material):
        self.counter += 1
        mesh = self.resource("SphereMesh", "radius = 1.0\nheight = 2.0\nradial_segments = 40\nrings = 20")
        self.node(f"{name}_{self.counter}", "MeshInstance3D", properties=f"position = Vector3{tuple(xyz)}\nscale = Vector3{tuple(scale)}\nmesh = {mesh}\nmaterial_override = {material}")


def build():
    from grass import write_assets
    from terrain import BANKS, height as terrain_height, write_assets as write_terrain
    RNG.seed(83742)
    s = Scene()
    ext = ['[ext_resource type="PackedScene" path="res://scenes/preview.tscn" id="preview"]']
    ext += [f'[ext_resource type="PackedScene" path="res://assets/models/{name}/{name}_1k.gltf" id="{name}"]' for name in ("pine_sapling_small", "boulder_01")]
    grass_patches = write_assets()
    grass_material = s.resource("StandardMaterial3D", 'albedo_color = Color(0.25, 0.34, 0.12, 1)\nroughness = 1.0\ncull_mode = 2')
    for index, patch in enumerate(grass_patches):
        ext.append(f'[ext_resource type="ArrayMesh" path="res://assets/vegetation/patch_{index:02d}.obj" id="grass{index}"]')
        x, z = patch["center"]
        s.node(f"GrassPatch_{index:02d}", "MeshInstance3D", properties=f'position = Vector3({x}, 0, {z})\nmesh = ExtResource("grass{index}")\nmaterial_override = {grass_material}')
    materials = {}
    for name in ("sparse_grass", "rock_01", "forest_floor", "rock_path", "weathered_planks"):
        for channel in ("diff", "nor_gl", "rough"):
            file = ROOT / f"assets/textures/{name}/{name}_{channel}_1k.jpg"
            if file.exists():
                ext.append(f'[ext_resource type="Texture2D" path="res://{file.relative_to(ROOT)}" id="{name}_{channel}"]')
        properties = f'albedo_texture = ExtResource("{name}_diff")\nnormal_enabled = true\nnormal_texture = ExtResource("{name}_nor_gl")\nuv1_scale = Vector3(0.3, 0.3, 0.3)\nuv1_triplanar = true'
        if (ROOT / f"assets/textures/{name}/{name}_rough_1k.jpg").exists():
            properties += f'\nroughness_texture = ExtResource("{name}_rough")'
        materials[name] = s.resource("StandardMaterial3D", properties)
    stone = materials["rock_01"]
    wood = materials["weathered_planks"]
    path = materials["rock_path"]
    grass = materials["sparse_grass"]
    write_terrain()
    for index, (cx, cz, radius, rise) in enumerate(BANKS):
        ext.append(f'[ext_resource type="ArrayMesh" path="res://assets/terrain/bank_{index}.obj" id="bank{index}"]')
        s.node(f"EarthBank_{index}", "MeshInstance3D", properties=f'position = Vector3({cx}, 0.003, {cz})\nmesh = ExtResource("bank{index}")\nmaterial_override = {grass}')
        # Reviewed client supports box collision only. Small low-rise cells keep
        # surface mismatch bounded; tests verify slope and maximum step height.
        for iz in range(8):
            for ix in range(8):
                x, z = cx-radius+(ix+0.5)*3, cz-radius+(iz+0.5)*3
                y = terrain_height(x,z)
                shape = s.resource("BoxShape3D", "size = Vector3(3, 0.4, 3)")
                name = f"BankFloor_{index}_{ix}_{iz}"
                s.node(name, "StaticBody3D", properties=f"position = Vector3({x}, {y-0.2}, {z})")
                s.node("Shape", "CollisionShape3D", name, f"shape = {shape}")
    dark = s.resource("StandardMaterial3D", "albedo_color = Color(0.055, 0.075, 0.09, 1)\nroughness = 0.7")
    gold = s.resource("StandardMaterial3D", "albedo_color = Color(0.6, 0.32, 0.09, 1)\nmetallic = 0.6\nroughness = 0.4")
    distant = s.resource("StandardMaterial3D", "albedo_color = Color(0.22, 0.31, 0.29, 1)\nroughness = 1.0")
    sky_blue = s.resource("StandardMaterial3D", "albedo_color = Color(0.38, 0.58, 0.76, 1)\nshading_mode = 0\ncull_mode = 1")
    # Reviewed static geometry supplies an actual sky in safe packages, whose
    # loader cannot yet reconstruct WorldEnvironment/Sky resources.
    s.ellipsoid("SkyDome", (0, 0, 0), (600, 600, 600), sky_blue)
    sky = s.resource("ProceduralSkyMaterial", "sky_top_color = Color(0.12, 0.22, 0.31, 1)\nsky_horizon_color = Color(0.63, 0.68, 0.69, 1)\nground_bottom_color = Color(0.13, 0.15, 0.14, 1)")
    sky_res = s.resource("Sky", f"sky_material = {sky}")
    environment = s.resource("Environment", f"background_mode = 2\nsky = {sky_res}\nambient_light_source = 3\nambient_light_color = Color(0.62, 0.7, 0.8, 1)\nambient_light_energy = 0.55\ntonemap_mode = 2\nfog_enabled = true\nfog_light_color = Color(0.36, 0.43, 0.46, 1)\nfog_density = 0.0015")
    s.node("Environment", "WorldEnvironment", properties=f"environment = {environment}")
    s.node("Sun", "DirectionalLight3D", properties="rotation_degrees = Vector3(-48, -35, 0)\nlight_color = Color(1, 0.96, 0.87, 1)\nlight_energy = 1.3\nshadow_enabled = true\ndirectional_shadow_max_distance = 180.0")
    s.node("SkyFill", "DirectionalLight3D", properties="rotation_degrees = Vector3(-60, 140, 0)\nlight_color = Color(0.65, 0.77, 1, 1)\nlight_energy = 0.65")
    s.node("Spawn", "Marker3D", properties='position = Vector3(0, 0.1, 95)\nmetadata/world_spawn = true\nmetadata/world_entity_id = "spawn"')
    s.box("Landscape", (0, -0.6, 15), (440, 1.2, 370), grass)
    # PBR paths follow the same authored graph used by navigation tests.
    for a, b in EDGES:
        ax, az = AREAS[a]
        bx, bz = AREAS[b]
        distance = math.hypot(bx-ax, bz-az)
        # One aligned trail ribbon per segment avoids the sawtooth tile edges.
        s.node(f"Route_{a}_{b}", "Node3D", properties=f"position = Vector3({(ax+bx)/2}, 0.012, {(az+bz)/2})\nrotation = Vector3(0, {math.atan2(bx-ax,bz-az)}, 0)")
        s.box("Trail", (0,0,0), (4.2, 0.024, distance + 2), path, False, f"Route_{a}_{b}")
        # Dark worn verges soften the hard path edge without alpha decals.
        s.box("WornVerge", (0,-0.007,0), (5.4, 0.008, distance+3), materials["forest_floor"], False, f"Route_{a}_{b}")
    # Real landmark geometry: buildings have door gaps rather than solid box walls.
    def clear_wall(name, xyz, size, material=None):
        # Preserve every authored route through ruins, including diagonal links.
        # Omit a wall segment if its footprint intersects a 2 m route clearance.
        x, _, z = xyz
        for a, b in EDGES:
            ax, az = AREAS[a]
            bx, bz = AREAS[b]
            steps = max(1, int(math.hypot(bx-ax, bz-az)))
            for step in range(steps + 1):
                px = ax + (bx-ax)*step/steps
                pz = az + (bz-az)*step/steps
                if abs(px-x) < size[0]/2+1.6 and abs(pz-z) < size[2]/2+1.6:
                    return
        s.box(name, xyz, size, material or stone)
        return True

    def ruin(name, x, z, width=18, depth=16, height=4, roof=False):
        s.box(name + "Floor", (x, 0.1, z), (width, 0.2, depth), path)
        for dx in (-width/2, width/2):
            # Split long side walls into short masonry bays for route openings.
            for dz in (-depth/3, 0, depth/3):
                clear_wall(name + "Side", (x+dx, height/2, z+dz), (0.7, height, depth/3))
        for dz in (-depth/2, depth/2):
            for dx in (-width/3, width/3):
                clear_wall(name + "DoorWall", (x+dx, height/2, z+dz), (width/3, height, 0.7))
            s.box(name + "Lintel", (x, height-0.35, z+dz), (width/3, 0.7, 0.7), stone)
        if roof:
            s.box(name + "Ceiling", (x, height+0.2, z), (width+0.6, 0.4, depth+0.6), stone)
    for name in ("farm", "village", "chapel", "watchtower"):
        x, z = AREAS[name]
        ruin(name, x, z, height=8 if name == "watchtower" else 4)
    for x, z in [(-18, -83), (20, -70), (-70, 76)]:
        ruin("Outbuilding", x, z, 9, 9, 2.5)
    # Stream runs across the field north edge; bridge and ford remain walkable.
    s.box("Stream", (5, 0.025, -5), (100, 0.05, 6), dark, False)
    s.box("BridgeDeck", (15, 0.18, -5), (7, 0.36, 12), wood)
    for x in (11.4, 18.6):
        for z in (-9, -5, -1):
            clear_wall("BridgeRail", (x, 0.9, z), (0.2, 1.0, 3.5))
    # Crypt is a roofed, walkable wing, not a teleport or a decorative sealed door.
    for name in ("crypt_entry", "galleries", "ossuary", "armory", "antechamber", "guardian"):
        x, z = AREAS[name]
        ruin(name, x, z, 21, 22, 5, True)
        s.node(name + "Lamp", "OmniLight3D", properties=f"position = Vector3({x}, 3, {z})\nlight_color = Color(1, 0.57, 0.24, 1)\nlight_energy = 4\nomni_range = 19")
    # Distinct original architecture assembled from audited stone/wood surfaces.
    # Details are placed on existing wall lines; route-clearance checks decide
    # which bays can safely contain structural projections.
    for name in ("farm", "village", "chapel", "watchtower", "crypt_entry", "galleries", "ossuary", "armory", "antechamber", "guardian"):
        x, z = AREAS[name]
        crypt = name in ("crypt_entry", "galleries", "ossuary", "armory", "antechamber", "guardian")
        width, depth = (21, 22) if crypt else (18, 16)
        height = 8 if name == "watchtower" else 5 if crypt else 4
        # Stone plinths and horizontal courses vary the masonry at player height.
        for side in (-1, 1):
            for offset in (-depth/3, 0, depth/3):
                for level in (0.3, 1.4, 2.7):
                    clear_wall("MasonryCourse", (x+side*width/2, level, z+offset), (0.82, 0.13, depth/3-0.15))
            if name in ("chapel", "crypt_entry", "guardian"):
                for offset in (-depth/2+2, depth/2-2):
                    clear_wall("Buttress", (x+side*(width/2+0.6), height/2, z+offset), (1.25, height, 1.3))
                    clear_wall("ButtressCap", (x+side*(width/2+0.6), height+0.1, z+offset), (1.45, 0.25, 1.55))
        # Heavy doorway frames read as entrances even when adjacent wall bays
        # are opened for diagonal routes. No trim crosses the walking opening.
        for side in (-1, 1):
            for dx in (-width/6-0.4, width/6+0.4):
                clear_wall("DoorJamb", (x+dx, 1.65, z+side*depth/2), (0.8, 3.3, 1.0))
            s.box("DoorCornice", (x, height+0.05, z+side*depth/2), (width/3+1.6, 0.25, 1.1), stone)
        if name in ("farm", "village", "chapel"):
            # Pitched timber framing and roof boards, not a solid block roof.
            for offset in (-depth/2, 0, depth/2):
                for side in (-1, 1):
                    parent = f"RoofFrame_{name}_{offset}_{side}".replace(".", "_")
                    s.node(parent, "Node3D", properties=f"position = Vector3({x+side*width/4}, {height+1.6}, {z+offset})\nrotation = Vector3(0, 0, {side*-0.34})")
                    s.box("RoofBeam", (0,0,0), (width/2+0.8, 0.24, 0.28), wood, False, parent)
            for side in (-1, 1):
                parent = f"RoofSlope_{name}_{side}"
                s.node(parent, "Node3D", properties=f"position = Vector3({x+side*width/4}, {height+1.6}, {z})\nrotation = Vector3(0, 0, {side*-0.34})")
                # Village/farm leave damaged gaps; chapel retains more shelter.
                for plank in range(9):
                    if name != "chapel" and plank in (2, 6): continue
                    s.box("RoofBoard", (0,0.13,-depth/2+plank*depth/8), (width/2+0.8, 0.14, depth/9), wood, False, parent)
        if crypt:
            # Ribbed ceilings and corner piers distinguish the interior wing.
            for offset in (-7, 0, 7):
                s.box("VaultRib", (x, 4.65, z+offset), (19.6, 0.25, 0.45), stone, False)
            for side in (-1, 1):
                for offset in (-7, 7):
                    clear_wall("CryptPier", (x+side*9.3, 2.2, z+offset), (0.8, 4.4, 0.9))
    # Four stations + adjacent spawn credits, all real preview interactions.
    for name in STATIONS + ["credits"]:
        x, z = AREAS["camp" if name == "credits" else name]
        x += -4 if name == "credits" else 4
        if name not in ("camp", "credits"):
            ax, az = AREAS[name]
            x, z = safe_offset(ax, az, (4,6))
        s.node("Station_" + name, "Node3D", properties=f'position = Vector3({x}, 0, {z})\nmetadata/title = "{name.replace("_", " ").title()} — {"Credits" if name == "credits" else "Leveling & map"}"\nmetadata/kind = "{"credits" if name == "credits" else "leveling"}"', groups=["stations"])
        s.box("Lectern", (x, 0.65, z), (1.1, 1.3, 0.8), stone)
        s.box("Book", (x, 1.34, z), (0.9, 0.08, 0.65), gold, False)
        s.label("CREDITS" if name == "credits" else "LEVELING / MAP", (x, 2.2, z), 28)
    # PBR prop groups give buildings a purpose, without cluttering travel lanes.
    for area in ("camp", "farm", "village", "chapel", "forecourt", "galleries", "armory", "ossuary"):
        ax, az = AREAS[area]
        for index in range(5):
            x, z = ax - 7 + index * 1.3, az + 5
            if clear_wall("Crate", (x, 0.55, z), (1.05, 1.1, 1.05), wood):
                s.box("CrateBand", (x, 0.6, z + 0.535), (1.1, 0.12, 0.04), gold, False)
        # Benches and tables: original joinery using audited wood materials.
        clear_wall("TableTop", (ax + 6, 0.95, az - 4), (2.4, 0.16, 1.2), wood)
        for dx in (5.1, 6.9):
            clear_wall("TableLeg", (ax + dx, 0.45, az - 4), (0.16, 0.9, 0.8), wood)
        clear_wall("Bench", (ax + 6, 0.5, az - 5.5), (2.5, 0.3, 0.55), wood)
    # Tangible world objects, not menu rewards. Existing client item transport
    # owns desktop/VR carrying; no custom physics scripts are packaged.
    for index, area in enumerate(("camp", "farm", "shrine", "watchtower", "village", "chapel", "forecourt", "crypt_entry", "galleries", "ossuary", "armory", "guardian")):
        ax, az = AREAS[area]
        name = f"Supply_{index:02d}"
        px, pz = safe_offset(ax, az, (6,6))
        s.node(name, "RigidBody3D", properties=f'position = Vector3({px}, 1.5, {pz})\nmass = 0.5\nmetadata/world_entity_id = "supply_{index:02d}"\nmetadata/world_pickup = true', groups=["world_items"])
        s.box("SupplyCase", (0, 0, 0), (0.45, 0.35, 0.35), wood, False, name)
        shape = s.resource("BoxShape3D", "size = Vector3(0.45, 0.35, 0.35)")
        s.node("Collision", "CollisionShape3D", name, f"shape = {shape}")
    # Imported scanned trees/rocks stay outside route corridors and door clearances.
    def route_distance(x, z):
        best = 1e9
        for a, b in EDGES:
            ax, az = AREAS[a]
            bx, bz = AREAS[b]
            vx, vz = bx-ax, bz-az
            t = max(0, min(1, ((x-ax)*vx+(z-az)*vz)/(vx*vx+vz*vz)))
            best = min(best, math.hypot(x-ax-t*vx, z-az-t*vz))
        return best
    tree_positions = []
    for index in range(1600):
        x, z = RNG.uniform(-209, 209), RNG.uniform(-160, 190)
        if route_distance(x,z) < 8 or any(math.hypot(x-ax,z-az)<16 for ax,az in AREAS.values()):
            continue
        # Preserve the central open meadow; build woodland belts around it.
        if -50 < x < 65 and -35 < z < 90: continue
        if any(math.hypot(x-px,z-pz) < 7 for px,pz in tree_positions): continue
        tree_positions.append((x,z))
        scale = RNG.uniform(14.0, 23.0)
        name = f"Pine_{index}"
        s.nodes.append(f'[node name="{name}" parent="." instance=ExtResource("pine_sapling_small")]\nposition = Vector3({x}, 0, {z})\nscale = Vector3({scale}, {scale}, {scale})\nrotation = Vector3(0, {RNG.uniform(0,6.28)}, 0)\n')
        if len(tree_positions) >= 115: break
    rock_positions = []
    for index in range(1000):
        x, z = RNG.uniform(-210, 210), RNG.uniform(-160, 190)
        if route_distance(x,z)<7 or any(math.hypot(x-ax,z-az)<15 for ax,az in AREAS.values()): continue
        if any(math.hypot(x-px,z-pz)<6 for px,pz in rock_positions): continue
        rock_positions.append((x,z))
        scale = RNG.uniform(1, 3)
        s.nodes.append(f'[node name="Rock_{index}" parent="." instance=ExtResource("boulder_01")]\nposition = Vector3({x}, 0, {z})\nscale = Vector3({scale}, {scale}, {scale})\n')
        if len(rock_positions) >= 75: break
    # Rounded foothills frame the map instead of a visible rectangular box wall.
    # Collision boundaries stay inside these overlapping visual mountain belts.
    for index in range(15):
        x = -250 + index * 36
        for z in (-200, 230):
            s.ellipsoid("Foothill", (x, -8, z), (RNG.uniform(35,55), RNG.uniform(20,42), 45), grass)
            s.ellipsoid("DistantPeak", (x, -5, z * 1.35), (60, RNG.uniform(45,85), 70), distant)
    for index in range(11):
        z = -175 + index * 38
        for x in (-250, 250):
            s.ellipsoid("Foothill", (x, -9, z), (45, RNG.uniform(22,40), 45), grass)
    for x in (-220, 220):
        s.box("Boundary", (x, 5, 15), (1, 10, 370), stone)
    for z in (-170, 200):
        s.box("Boundary", (0, 5, z), (440, 10, 1), stone)
    for name, (x,z) in AREAS.items():
        s.label(name.replace("_", " ").upper(), (x, 4, z))
        s.node("Area_" + name, "Marker3D", properties=f'position = Vector3({x}, 0.5, {z})\nmetadata/area_id = "{name}"', groups=["areas"])
    s.nodes.append('[node name="Preview" parent="." instance=ExtResource("preview")]\n')
    text = '[gd_scene format=3]\n\n' + '\n'.join(ext + s.resources) + '\n[node name="AshenVale" type="Node3D"]\n\n' + '\n'.join(s.nodes)
    (ROOT / "scenes/world.tscn").write_text(text)
    (ROOT / "map.json").write_text(json.dumps({"areas": AREAS, "routes": EDGES, "stations": STATIONS, "spawn": "camp", "exit": "guardian", "size_m": [440,370], "trees": len(tree_positions), "rocks": len(rock_positions), "pickup_items": 12, "grass_patches": len(grass_patches), "grass_blades": sum(len(p["blades"]) for p in grass_patches)}, indent=2) + '\n')
    print(f"Built {len(AREAS)} areas, {len(EDGES)} routes, {len(s.nodes)} scene nodes")


if __name__ == "__main__":
    build()
