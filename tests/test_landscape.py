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


if __name__ == "__main__":
    unittest.main()
