#!/usr/bin/env python3
"""Test actual exported world with a read-only copy of Comunicare production code."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comunicare", type=Path, required=True)
    parser.add_argument("--package", type=Path, default=ROOT / "build/ember-crypt.cworld")
    args = parser.parse_args()
    with zipfile.ZipFile(args.package) as archive:
        forbidden = [name for name in archive.namelist() if name.endswith((".gd", ".gltf", ".glb", ".bin", ".jpg", ".import")) or name in ("project.godot",)]
        if forbidden:
            raise ValueError(f"Unsafe/unconverted package files: {forbidden}")
    with tempfile.TemporaryDirectory(prefix="ember-client-", dir="/tmp/opencode") as folder:
        folder = Path(folder)
        project = folder / "project"
        project.mkdir()
        shutil.copytree(args.comunicare / "scripts/worlds", project / "scripts/worlds", ignore=shutil.ignore_patterns("*.uid"))
        # The VR menu resource is copied for path resolution; headset behavior is
        # not exercised and this does not run application startup/autoloads.
        shutil.copytree(args.comunicare / "scenes/GUI", project / "scenes/GUI")
        shutil.copy2(ROOT / "tests/package_suite.gd", project / "suite.gd")
        shutil.copy2(args.package, project / "ember-crypt.cworld")
        (project / "project.godot").write_text('config_version=5\n[application]\nconfig/name="Ember Comunicare integration"\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
        env = os.environ.copy()
        for key in ("HOME", "XDG_DATA_HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME"):
            target = folder / key
            target.mkdir()
            env[key] = str(target)
        # Do not import unrelated client GUI scenes/autoloads in this fixture.
        for flags in (["--script", "res://suite.gd"],):
            result = subprocess.run([os.environ.get("GODOT", "godot"), "--headless", "--path", str(project), *flags], env=env, capture_output=True, text=True, timeout=180)
            output = result.stdout + result.stderr
            print(output)
            if "ERROR:" in output or result.returncode not in (0, 1): return 2
            if result.returncode: return 1
            if "Comunicare package:" not in output: return 2
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(f"Infrastructure failure: {error}")
        raise SystemExit(2)
