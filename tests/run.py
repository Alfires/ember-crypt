#!/usr/bin/env python3
"""Import/run a disposable map copy, keeping caches and user state out of source."""
import json
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    inventory = json.loads((ROOT / "assets/provenance.json").read_text())
    count = 0
    for asset in inventory["assets"]:
        for item in asset["files"]:
            if hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() != item["sha256"]:
                raise ValueError(f"Asset hash mismatch: {item['path']}")
            count += 1
    print(f"Asset provenance: {count} hashes verified")
    with tempfile.TemporaryDirectory(prefix="ember-map-", dir="/tmp/opencode") as folder:
        project = Path(folder) / "project"
        shutil.copytree(ROOT, project, ignore=shutil.ignore_patterns(".git", ".godot", "*.import", "__pycache__", "build"))
        env = os.environ.copy()
        for key in ("HOME", "XDG_DATA_HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME"):
            path = Path(folder) / key
            path.mkdir()
            env[key] = str(path)
        for args in (["--editor", "--import"], ["--script", "res://tests/map_suite.gd"], ["--script", "res://tests/progression_suite.gd"], ["--script", "res://tests/menu_suite.gd"], ["--quit-after", "5"]):
            result = subprocess.run([os.environ.get("GODOT", "godot"), "--headless", "--path", str(project), *args], env=env, capture_output=True, text=True, timeout=180)
            output = result.stdout + result.stderr
            if "--editor" not in args or result.returncode or "ERROR:" in output:
                print(output)
            if "ERROR:" in output or result.returncode not in (0, 1):
                return 2
            if result.returncode:
                return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(f"Infrastructure failure: {error}")
        raise SystemExit(2)
