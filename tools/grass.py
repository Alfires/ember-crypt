#!/usr/bin/env python3
"""Original bent-blade vegetation, authored into bounded static OBJ patches."""
import math
from pathlib import Path
import random

from build_map import AREAS, EDGES

ROOT = Path(__file__).resolve().parents[1]


def route_distance(x, z):
    best = math.inf
    for a, b in EDGES:
        ax, az = AREAS[a]
        bx, bz = AREAS[b]
        vx, vz = bx - ax, bz - az
        t = max(0, min(1, ((x-ax)*vx + (z-az)*vz)/(vx*vx+vz*vz)))
        best = min(best, math.hypot(x-ax-t*vx, z-az-t*vz))
    return best


def allowed(x, z):
    if not (-210 < x < 210 and -155 < z < 185):
        return False
    if route_distance(x, z) < 3.4:
        return False
    if -47 < x < 57 and -9 < z < -1:  # water/bridge approaches
        return False
    # Floors, outbuildings, stations and loose supplies stay clear.
    for ax, az in [*AREAS.values(), (-18, -83), (20, -70), (-70, 76)]:
        if abs(x-ax) < 14 and abs(z-az) < 14:
            return False
    return True


def generate():
    rng = random.Random(487190)
    centers = []
    # Dense foreground banks and meadow islands, then woodland verge patches.
    for z in range(-115, 166, 20):
        for x in range(-165, 186, 20):
            weight = math.exp(-((x/100)**2 + ((z-45)/105)**2))
            if rng.random() < weight * 0.95:
                centers.append((x + rng.uniform(-4, 4), z + rng.uniform(-4, 4)))
    patches = []
    for cx, cz in centers[:64]:
        blades = []
        for _ in range(1400):
            x, z = cx + rng.uniform(-11, 11), cz + rng.uniform(-11, 11)
            # Organic, irregular patch outline instead of a square footprint.
            radius = 8.5 + 2 * math.sin(x * 0.7) * math.cos(z * 0.5)
            if math.hypot(x-cx, z-cz) > radius or not allowed(x, z):
                continue
            blades.append((x, z, rng.uniform(0.22, 0.5), rng.uniform(0, math.tau), rng.uniform(0.008, 0.024)))
            if len(blades) == 360:
                break
        if len(blades) > 100:
            patches.append({"center": (cx, cz), "blades": blades})
    return patches


def write_assets():
    folder = ROOT / "assets/vegetation"
    folder.mkdir(exist_ok=True)
    # Three restrained tones reduce uniformity; no alpha cards or custom shaders.
    (folder / "grass.mtl").write_text("\n".join(
        f"newmtl grass{i}\nKd {r} {g} {b}\nKs 0 0 0\nNs 1\n"
        for i, (r,g,b) in enumerate(((0.18,0.27,0.08),(0.27,0.34,0.12),(0.38,0.37,0.17)))
    ))
    patches = generate()
    for index, patch in enumerate(patches):
        cx, cz = patch["center"]
        # Up-biased normals approximate a dense tuft's diffuse response instead
        # of making half the thin double-sided blades shade almost black.
        lines = ["mtllib grass.mtl", "o GrassPatch", "usemtl grass0", "vn 0 1 0"]
        for n, (x,z,height,angle,width) in enumerate(patch["blades"]):
            dx, dz = math.cos(angle)*width, math.sin(angle)*width
            bend_x, bend_z = math.sin(angle)*height*0.25, math.cos(angle)*height*0.25
            vertices = [
                (x-cx-dx, 0.008, z-cz-dz), (x-cx+dx, 0.008, z-cz+dz),
                (x-cx+dx*0.5+bend_x*0.4, height*0.6, z-cz+dz*0.5+bend_z*0.4),
                (x-cx-dx*0.5+bend_x*0.4, height*0.6, z-cz-dz*0.5+bend_z*0.4),
                (x-cx+bend_x, height, z-cz+bend_z),
            ]
            lines += [f"v {a:.5f} {b:.5f} {c:.5f}" for a,b,c in vertices]
            start = n*5+1
            lines += [f"f {start}//1 {start+1}//1 {start+2}//1", f"f {start}//1 {start+2}//1 {start+3}//1", f"f {start+3}//1 {start+2}//1 {start+4}//1"]
        (folder / f"patch_{index:02d}.obj").write_text("\n".join(lines) + "\n")
    return patches


if __name__ == "__main__":
    patches = write_assets()
    print(f"Generated {len(patches)} grass patches, {sum(len(p['blades']) for p in patches)} blades")
