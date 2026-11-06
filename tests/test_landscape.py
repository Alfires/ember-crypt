"""Deterministic vegetation placement contracts, independent of Godot rendering."""
import importlib.util
from pathlib import Path
import unittest
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
spec = importlib.util.spec_from_file_location("landscape", ROOT / "tools/grass.py")


class LandscapeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def test_determinism(self):
        self.assertEqual(self.module.generate(), self.module.generate())

    def test_grounded_varied_blades(self):
        patches = self.module.generate()
        blades = [blade for patch in patches for blade in patch["blades"]]
        self.assertGreater(len(blades), 12000)
        self.assertLess(len(blades), 24000)
        self.assertGreater(len({round(b[2], 2) for b in blades}), 20)
        self.assertTrue(all(0.2 <= b[2] <= 0.75 for b in blades))

    def test_clearance(self):
        for patch in self.module.generate():
            for x, z, *_ in patch["blades"]:
                self.assertTrue(self.module.allowed(x, z))
                self.assertGreaterEqual(self.module.route_distance(x, z), 3.4)

    def test_budget(self):
        patches = self.module.generate()
        self.assertLessEqual(len(patches), 64)
        self.assertLessEqual(sum(len(p["blades"]) for p in patches) * 5, 120000)

    def test_terrain_safe_slopes_and_flat_routes(self):
        from terrain import height, BANKS
        self.assertEqual(height(0, 95), 0)
        for cx, cz, radius, rise in BANKS:
            self.assertAlmostEqual(height(cx, cz), rise)
            self.assertEqual(height(cx+radius, cz), 0)
            for ix in range(-12, 13):
                for iz in range(-12, 13):
                    x, z = cx+ix, cz+iz
                    self.assertLess(abs(height(x+0.1,z)-height(x,z))/0.1, 0.15)
                    self.assertLess(abs(height(x,z+0.1)-height(x,z))/0.1, 0.15)
        # Ground under authored roads stays flat; no collision banks at stations.
        from build_map import AREAS, EDGES
        for a,b in EDGES:
            ax,az = AREAS[a]
            bx,bz = AREAS[b]
            for step in range(101):
                self.assertLess(height(ax+(bx-ax)*step/100, az+(bz-az)*step/100), 0.01)


if __name__ == "__main__":
    unittest.main()
