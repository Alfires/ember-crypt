#!/usr/bin/env python3
"""Vendor only audited CC0 sources from a local Comunicare checkout."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = Path(sys.argv[1])
    inventory = json.loads((source / "assets/welcome_island/manifest.json").read_text())
    selected = {"polyhaven.pine_sapling_small", "polyhaven.boulder_01"}
    # Include the existing audited PBR surface entries, not their import caches.
    texture_names = {"forest_floor", "rock_01", "rock_path", "sparse_grass", "weathered_planks"}
    assets = []
    for entry in inventory["assets"]:
        if entry["id"] not in selected and not any(
            f"/textures/{name}/" in f["path"] for name in texture_names for f in entry["files"]
        ):
            continue
        record = {k: entry[k] for k in ("id", "title", "author", "source", "license", "retrieved")}
        record["modifications"] = "Source model/texture files unchanged; no derived runtime scenes copied."
        record["files"] = []
        for item in entry["files"]:
            relative = item["path"].replace("assets/welcome_island/", "assets/")
            if "/runtime/" in relative:
                continue
            data = (source / item["path"]).read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            if digest != item["sha256"]:
                raise ValueError(f"Source hash mismatch: {item['path']}")
            target = ROOT / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            record["files"].append({"path": relative, "sha256": digest, "download": item.get("download", "")})
        assets.append(record)
    license_file = ROOT / "assets/licenses/CC0-1.0.txt"
    license_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / "assets/welcome_island/licenses/CC0-1.0.txt", license_file)
    (ROOT / "assets/provenance.json").write_text(json.dumps({"assets": assets}, indent=2) + "\n")
    print(f"Vendored {len(assets)} audited CC0 asset groups")


if __name__ == "__main__":
    main()
