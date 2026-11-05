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
}
EDGES = [
    ("camp", "south_road"), ("south_road", "field"), ("south_road", "farm"),
    ("farm", "shrine"), ("shrine", "woodland"), ("woodland", "watchtower"),
    ("shrine", "field"), ("watchtower", "village"), ("field", "ford"),
    ("field", "bridge"), ("bridge", "village"), ("village", "chapel"),
    ("chapel", "forecourt"), ("bridge", "forecourt"), ("forecourt", "crypt_entry"),
    ("crypt_entry", "galleries"), ("galleries", "ossuary"), ("galleries", "armory"),
    ("ossuary", "antechamber"), ("armory", "antechamber"), ("antechamber", "guardian"),
]
STATIONS = ["camp", "shrine", "chapel", "crypt_entry"]


class Scene:
    def __init__(self):
        self.resources = []
        self.nodes = []
        self.counter = 0

    def resource(self, kind, properties):
        key = f"r{len(self.resources)}"
        self.resources.append(f'[sub_resource type="{kind}" id="{key}"]\n{properties}\n')
        return f'SubResource("{key}")'

    def node(self, name, kind, parent=".", properties="", groups=None):
        extra = f' groups={json.dumps(groups)}' if groups else ""
        self.nodes.append(f'[node name="{name}" type="{kind}" parent="{parent}"{extra}]\n{properties}\n')

    def box(self, name, xyz, size, material, collision=True, parent="."):
        self.counter += 1
        name = f"{name}_{self.counter}"
        mesh = self.resource("BoxMesh", f"size = Vector3{tuple(size)}")
        self.node(name, "MeshInstance3D", parent, f"position = Vector3{tuple(xyz)}\nmesh = {mesh}\nmaterial_override = {material}")
        if collision:
            shape = self.resource("BoxShape3D", f"size = Vector3{tuple(size)}")
            path = name if parent == "." else parent + "/" + name
            self.node("Body", "StaticBody3D", path)
            self.node("Collision", "CollisionShape3D", path + "/Body", f"shape = {shape}")

    def label(self, text, xyz, size=40):
        self.counter += 1
        self.node(f"Label_{self.counter}", "Label3D", properties=f"position = Vector3{tuple(xyz)}\ntext = {json.dumps(text)}\nfont_size = {size}\npixel_size = 0.012\nbillboard = 1\nmodulate = Color(0.91, 0.83, 0.64, 1)")


def build():
    s = Scene()
    ext = ['[ext_resource type="PackedScene" path="res://scenes/preview.tscn" id="preview"]']
    ext += [f'[ext_resource type="PackedScene" path="res://assets/models/{name}/{name}_1k.gltf" id="{name}"]' for name in ("pine_sapling_small", "boulder_01")]
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
    dark = s.resource("StandardMaterial3D", "albedo_color = Color(0.055, 0.075, 0.09, 1)\nroughness = 0.7")
    gold = s.resource("StandardMaterial3D", "albedo_color = Color(0.6, 0.32, 0.09, 1)\nmetallic = 0.6\nroughness = 0.4")
    sky = s.resource("ProceduralSkyMaterial", "sky_top_color = Color(0.12, 0.22, 0.31, 1)\nsky_horizon_color = Color(0.63, 0.68, 0.69, 1)\nground_bottom_color = Color(0.13, 0.15, 0.14, 1)")
    sky_res = s.resource("Sky", f"sky_material = {sky}")
    environment = s.resource("Environment", f"background_mode = 2\nsky = {sky_res}\nambient_light_source = 3\nambient_light_color = Color(0.62, 0.7, 0.8, 1)\nambient_light_energy = 0.55\ntonemap_mode = 2\nfog_enabled = true\nfog_light_color = Color(0.36, 0.43, 0.46, 1)\nfog_density = 0.0015")
    s.node("Environment", "WorldEnvironment", properties=f"environment = {environment}")
    s.node("Sun", "DirectionalLight3D", properties="rotation_degrees = Vector3(-42, -35, 0)\nlight_color = Color(1, 0.85, 0.65, 1)\nlight_energy = 1.5\nshadow_enabled = true\ndirectional_shadow_max_distance = 180.0")
    s.node("Spawn", "Marker3D", properties='position = Vector3(0, 0.1, 95)\nmetadata/world_spawn = true\nmetadata/world_entity_id = "spawn"')
    s.box("Landscape", (0, -0.6, 15), (300, 1.2, 270), grass)
    # PBR paths follow the same authored graph used by navigation tests.
    for a, b in EDGES:
        ax, az = AREAS[a]
        bx, bz = AREAS[b]
        distance = math.hypot(bx-ax, bz-az)
        count = max(1, int(distance / 3))
        for step in range(count + 1):
            t = step / count
            s.box("Trail", (ax + (bx-ax)*t, 0.012, az + (bz-az)*t), (5, 0.024, 5), path, False)
    # Real landmark geometry: buildings have door gaps rather than solid box walls.
    def clear_wall(name, xyz, size):
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
                if abs(px-x) < size[0]/2+1 and abs(pz-z) < size[2]/2+1:
                    return
        s.box(name, xyz, size, stone)

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
    # Four stations + adjacent spawn credits, all real preview interactions.
    for name in STATIONS + ["credits"]:
        x, z = AREAS["camp" if name == "credits" else name]
        x += -4 if name == "credits" else 4
        if name not in ("camp", "credits"):
            z += 6
        s.node("Station_" + name, "Node3D", properties=f'position = Vector3({x}, 0, {z})\nmetadata/title = "{name.replace("_", " ").title()} — {"Credits" if name == "credits" else "Leveling & map"}"\nmetadata/kind = "{"credits" if name == "credits" else "leveling"}"', groups=["stations"])
        s.box("Lectern", (x, 0.65, z), (1.1, 1.3, 0.8), stone)
        s.box("Book", (x, 1.34, z), (0.9, 0.08, 0.65), gold, False)
        s.label("CREDITS" if name == "credits" else "LEVELING / MAP", (x, 2.2, z), 28)
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
    for index in range(85):
        x, z = RNG.uniform(-140, 50), RNG.uniform(-110, 125)
        if route_distance(x,z) < 9 or any(math.hypot(x-ax,z-az)<16 for ax,az in AREAS.values()):
            continue
        # Dense woodland to the west, sparse meadow silhouettes elsewhere.
        if x > -50 and index % 4: continue
        scale = RNG.uniform(1.8, 3.5)
        name = f"Pine_{index}"
        s.nodes.append(f'[node name="{name}" parent="." instance=ExtResource("pine_sapling_small")]\nposition = Vector3({x}, 0, {z})\nscale = Vector3({scale}, {scale}, {scale})\nrotation = Vector3(0, {RNG.uniform(0,6.28)}, 0)\n')
    for index in range(45):
        x, z = RNG.uniform(-145, 60), RNG.uniform(-110, 125)
        if route_distance(x,z)<7: continue
        scale = RNG.uniform(1, 3)
        s.nodes.append(f'[node name="Rock_{index}" parent="." instance=ExtResource("boulder_01")]\nposition = Vector3({x}, 0, {z})\nscale = Vector3({scale}, {scale}, {scale})\n')
    # Boundary walls make the map finite without allowing falls out of the world.
    for x in (-150, 150): s.box("Cliff", (x, 5, 15), (3, 10, 270), stone)
    for z in (-120, 150): s.box("Cliff", (0, 5, z), (300, 10, 3), stone)
    for name, (x,z) in AREAS.items():
        s.label(name.replace("_", " ").upper(), (x, 4, z))
        s.node("Area_" + name, "Marker3D", properties=f'position = Vector3({x}, 0.5, {z})\nmetadata/area_id = "{name}"', groups=["areas"])
    s.nodes.append('[node name="Preview" parent="." instance=ExtResource("preview")]\n')
    text = '[gd_scene format=3]\n\n' + '\n'.join(ext + s.resources) + '\n[node name="AshenVale" type="Node3D"]\n\n' + '\n'.join(s.nodes)
    (ROOT / "scenes/world.tscn").write_text(text)
    (ROOT / "map.json").write_text(json.dumps({"areas": AREAS, "routes": EDGES, "stations": STATIONS, "spawn": "camp", "exit": "guardian"}, indent=2) + '\n')
    print(f"Built {len(AREAS)} areas, {len(EDGES)} routes, {len(s.nodes)} scene nodes")


if __name__ == "__main__":
    build()
