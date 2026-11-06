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
    parser.add_argument("--render", action="store_true", help="Also capture real package views using the available display")
    parser.add_argument("--view", choices=["chapel", "crypt_interior", "grass_detail", "camp", "field", "woodland", "overview"], help="Capture only this view (requires --render)")
    parser.add_argument("--suite", choices=["all", "package", "loop", "interaction"], default="all", help="Run a focused integration suite or all")
    args = parser.parse_args()
    with zipfile.ZipFile(args.package) as archive:
        forbidden = [name for name in archive.namelist() if name.endswith((".gd", ".gltf", ".glb", ".bin", ".jpg", ".import")) or name in ("project.godot",)]
        if forbidden:
            raise ValueError(f"Unsafe/unconverted package files: {forbidden}")
    temporary_root = ROOT / "build/test-tmp"
    temporary_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ember-client-", dir=temporary_root) as folder:
        folder = Path(folder)
        project = folder / "project"
        project.mkdir()
        shutil.copytree(args.comunicare / "scripts/worlds", project / "scripts/worlds", ignore=shutil.ignore_patterns("*.uid"))
        # The VR menu resource is copied for path resolution; headset behavior is
        # not exercised and this does not run application startup/autoloads.
        shutil.copytree(args.comunicare / "scenes/GUI", project / "scenes/GUI")
        shutil.copy2(ROOT / "tests/package_suite.gd", project / "suite.gd")
        shutil.copy2(ROOT / "tests/loop_suite.gd", project / "loop_suite.gd")
        shutil.copy2(ROOT / "tests/interaction_suite.gd", project / "interaction_suite.gd")
        shutil.copy2(ROOT / "tests/render_package.gd", project / "render.gd")
        shutil.copy2(args.package, project / "ember-crypt.cworld")
        (project / "project.godot").write_text('config_version=5\n[application]\nconfig/name="Ember Comunicare integration"\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
        env = os.environ.copy()
        for key in ("HOME", "XDG_DATA_HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME"):
            target = folder / key
            target.mkdir()
            env[key] = str(target)
        # Do not import unrelated client GUI scenes/autoloads in this fixture.
        for script, marker in [("suite.gd", "Comunicare package:"), ("loop_suite.gd", "World objective loop:"), ("interaction_suite.gd", "World interactions:")]:
            if args.suite == "package" and script != "suite.gd": continue
            if args.suite == "loop" and script != "loop_suite.gd": continue
            if args.suite == "interaction" and script != "interaction_suite.gd": continue
            flags = ["--script", "res://" + script]
            print("Running Comunicare integration:", script, flush=True)
            try:
                result = subprocess.run([os.environ.get("GODOT", "godot"), "--headless", "--path", str(project), *flags], env=env, capture_output=True, text=True, timeout=180)
            except subprocess.TimeoutExpired as error:
                # Keep partial assertion output: a stalled runtime must not hide
                # the last completed check or look like a successful empty run.
                for partial in (error.stdout, error.stderr):
                    if partial:
                        print(partial.decode(errors="replace") if isinstance(partial, bytes) else partial)
                raise
            output = result.stdout + result.stderr
            print(output)
            if "ERROR:" in output or result.returncode not in (0, 1): return 2
            if result.returncode: return 1
            if marker not in output: return 2
        if args.render:
            target = ROOT / "build/review"
            target.mkdir(parents=True, exist_ok=True)
            command = [os.environ.get("GODOT", "godot"), "--path", str(project), "--script", "res://render.gd", "--", str(target)]
            if args.view: command.append(args.view)
            result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=180)
            output = result.stdout + result.stderr
            print(output)
            if "ERROR:" in output or result.returncode: return 2
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(f"Infrastructure failure: {error}")
        raise SystemExit(2)
