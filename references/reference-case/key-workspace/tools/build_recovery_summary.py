#!/usr/bin/env python3
"""Write a compact summary of the Griddle recovery outputs."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("output/recovery-summary.json"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.workspace.resolve()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    with (root / "output" / "level-inventory.json").open() as handle:
        inventory = json.load(handle)
    with (root / "output" / "level-map.json").open() as handle:
        level_map = json.load(handle)
    with (root / "output" / "assets-index.json").open() as handle:
        asset_index = json.load(handle)
    with (root / "output" / "unity-extract" / "manifest.json").open() as handle:
        unity_manifest = json.load(handle)

    report = (root / "output" / "levels" / "_download-report.txt").read_text().splitlines()
    download = Counter(line.split("\t")[1] for line in report if "\t" in line)
    image_types = {"Texture2D", "Sprite"}
    image_records = sum(
        1 for record in unity_manifest["records"] if record["type"] in image_types
    )
    ipa = root / "device" / "Griddle-256.ipa"

    summary = {
        "app": "Griddle! (com.games.griddle, version 256)",
        "ipa_path": "device/Griddle-256.ipa",
        "ipa_bytes": ipa.stat().st_size if ipa.exists() else None,
        "level_downloads": {
            "total": len(report),
            "ok": download.get("ok", 0),
            "failed": sum(count for status, count in download.items() if status != "ok"),
        },
        "levels": {
            "catalog_levels": inventory["catalog_level_count"],
            "local_revisions": inventory["local_only_count"],
            "revision_count": inventory["entry_count"],
        },
        "levels_encrypted": {
            "decoded_count": len(
                list((root / "output" / "levels-encrypted").glob("*.bin"))
            ),
            "directory": "output/levels-encrypted",
        },
        "unity_extract": {
            "asset_files": unity_manifest["summary"]["asset_file_count"],
            "object_count": unity_manifest["summary"]["object_count"],
            "record_count": unity_manifest["summary"]["record_count"],
            "image_records": image_records,
            "failure_count": unity_manifest["summary"]["failure_count"],
        },
        "assets": {
            "unique_cgasset_ids": asset_index["unique_cgasset_ids"],
            "unique_local_sprites": asset_index["unique_local_sprites"],
            "missing_sprites": sum(
                len(item["missing_sprites"]) for item in asset_index["levels"]
            ),
        },
        "maps": {
            "level_map_revisions": level_map["revision_count"],
            "level_map_bundles": level_map["bundle_count"],
            "catalog_level_matches": level_map["catalog_level_matches"],
        },
        "artifacts": {
            "level_inventory": "output/level-inventory.json",
            "level_map": "output/level-map.json",
            "assets_index": "output/assets-index.json",
            "unity_manifest": "output/unity-extract/manifest.json",
            "levels_dir": "output/levels",
            "levels_encrypted_dir": "output/levels-encrypted",
        },
    }
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
