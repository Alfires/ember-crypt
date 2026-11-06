"""Low rolling earth banks with an explicit, testable walkable height function."""
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Away from buildings, water and main trail centerlines. Heights deliberately low
# until the client supports general triangle-mesh terrain collision.
BANKS = [(-35.0, 48.0, 12.0, 0.65), (48.0, 65.0, 12.0, 0.55), (-55.0, -12.0, 12.0, 0.6)]


def height(x, z):
    value = 0.0
    for cx, cz, radius, rise in BANKS:
        dx, dz = (x-cx)/radius, (z-cz)/radius
        if abs(dx) < 1 and abs(dz) < 1:
            value += rise * (math.cos(dx*math.pi)+1)/2 * (math.cos(dz*math.pi)+1)/2
    return value


def write_assets():
    folder = ROOT / "assets/terrain"
    folder.mkdir(exist_ok=True)
    for index, (cx, cz, radius, _) in enumerate(BANKS):
        lines = ["o EarthBank"]
        steps = 24
        for iz in range(steps+1):
            for ix in range(steps+1):
                x, z = -radius + ix*radius*2/steps, -radius + iz*radius*2/steps
                y = height(cx+x, cz+z)
                lines += [f"v {x:.6f} {y:.6f} {z:.6f}", f"vt {(cx+x)*0.3:.6f} {(cz+z)*0.3:.6f}"]
        for iz in range(steps):
            for ix in range(steps):
                a = iz*(steps+1)+ix+1
                b, c, d = a+1, a+steps+1, a+steps+2
                lines += [f"f {a}/{a} {c}/{c} {b}/{b}", f"f {b}/{b} {c}/{c} {d}/{d}"]
        (folder / f"bank_{index}.obj").write_text("\n".join(lines)+"\n")
