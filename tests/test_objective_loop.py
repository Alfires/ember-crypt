"""Pure author-data regression tests; not a replacement for the real client VM/store."""
import itertools
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from objective_loop import add_loop
from package_world import world_logic

RELICS = ("relic_watchtower", "relic_village", "relic_forecourt")


def apply(operations, saved):
    """Interpret only generated objective operations, using the VM's input snapshot."""
    original = saved.copy()
    next_saved = saved.copy()
    pages = []

    def execute(block):
        for instruction in block:
            op = instruction["op"]
            if op == "if_saved":
                branch = "then" if original.get(instruction["key"]) == instruction["equals"] else "else"
                execute(instruction[branch])
            elif op == "save_set":
                next_saved[instruction["key"]] = instruction["value"]
            elif op == "save_add":
                key = instruction["key"]
                next_saved[key] = next_saved.get(key, 0) + instruction["value"]
            elif op == "menu":
                pages.append(instruction["page"])
            else:
                raise AssertionError("Unexpected objective instruction: " + op)

    execute(operations)
    return next_saved, pages


class ObjectiveLoopTests(unittest.TestCase):
    def setUp(self):
        self.pages = {"overview": {"widgets": [{"id": "description", "text": ""}]}}
        self.programs = add_loop(self.pages)
        self.start = self.pages["overview"]["widgets"][1]["actions"]

    def test_objectives_require_start_and_all_three_seals(self):
        for program in self.programs.values():
            self.assertEqual(apply(program, {}), ({}, ["locked"]))
        for flags in itertools.product((False, True), repeat=3):
            saved = {"run_active": True, **dict(zip(RELICS, flags))}
            after, pages = apply(self.programs["altar"], saved)
            self.assertEqual(pages, ["victory" if all(flags) else "locked"])
            if not all(flags):
                self.assertEqual(after, saved)

    def test_every_relic_order_awards_once_and_finishes_once(self):
        for order in itertools.permutations(RELICS):
            saved, _ = apply(self.start, {})
            for index, relic in enumerate(order, 1):
                saved, pages = apply(self.programs[relic], saved)
                self.assertEqual(pages, ["objectives"])
                self.assertEqual(saved["run_xp"], index * 25)
                self.assertEqual(apply(self.programs[relic], saved)[0], saved)
            saved, pages = apply(self.programs["altar"], saved)
            self.assertEqual((saved["wins"], saved["run_active"], pages), (1, False, ["victory"]))
            self.assertEqual(apply(self.programs["altar"], saved), (saved, ["locked"]))

    def test_restart_preserves_other_saved_data_and_clears_seals(self):
        old = {"wins": 7, "map_note": "Keep this", "run_xp": 75, **dict.fromkeys(RELICS, True)}
        saved, pages = apply(self.start, old)
        self.assertEqual((saved["wins"], saved["map_note"]), (7, "Keep this"))
        self.assertEqual((saved["run_active"], saved["run_xp"], pages), (True, 0, ["objectives"]))
        self.assertTrue(all(saved[key] is False for key in RELICS))
        self.assertEqual(apply(self.programs["altar"], saved), (saved, ["locked"]))

    def test_package_ui_stays_within_current_client_limits(self):
        with tempfile.TemporaryDirectory(prefix="ember-loop-data-", dir="/tmp/opencode") as directory:
            destination = Path(directory)
            world_logic(destination)
            pages = json.loads((destination / "ui/menu.worldui").read_text())["pages"]
            self.assertLessEqual(len(pages), 16)
            self.assertLessEqual(sum(len(page["widgets"]) for page in pages.values()), 128)
            self.assertEqual(set(self.programs), {path.stem for path in (destination / "logic").glob("*.worldscript")} - {"camp", "shrine", "chapel", "crypt_entry", "credits"})
            for page in pages.values():
                ids = [widget["id"] for widget in page["widgets"]]
                self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()
