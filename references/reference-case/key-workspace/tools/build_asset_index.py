#!/usr/bin/env python3
"""Index level JSON cgasset ids against exported local sprite files."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


SPRITE_NAME_RE = re.compile(r"^([0-9A-F]{64})__")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--levels", type=Path, required=True)
    parser.add_argument("--sprites", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("output/assets-index.json"))
    return parser.parse_args()


def collect_ids(level: dict[str, object]) -> set[str]:
    ids: set[str] = set()
    if level.get("poster_image_cgasset_id"):
        ids.add(level["poster_image_cgasset_id"])
    for item in level.get("items", []):
        if item.get("image_cgasset_id"):
            ids.add(item["image_cgasset_id"])
    for clue in level.get("clues", []):
        if clue.get("image_cgasset_id"):
            ids.add(clue["image_cgasset_id"])
        for asset in clue.get("assets", []):
            if isinstance(asset, dict) and asset.get("image_cgasset_id"):
                ids.add(asset["image_cgasset_id"])
    catalog = level.get("cgasset_catalog", {})
    if isinstance(catalog, dict):
        ids.update(catalog.get("assets", {}).keys())
    return ids


def main() -> int:
    args = parse_args()
    sprite_by_id: dict[str, list[str]] = defaultdict(list)
    for path in args.sprites.glob("*.png"):
        match = SPRITE_NAME_RE.match(path.name)
        if match:
            sprite_by_id[match.group(1)].append(path.name)

    all_ids: set[str] = set()
    levels: list[dict[str, object]] = []
    for path in sorted(args.levels.glob("*.json")):
        if path.name == "_download-report.txt":
            continue
        with path.open() as handle:
            level = json.load(handle)
        ids = collect_ids(level)
        all_ids.update(ids)
        missing = sorted(asset_id for asset_id in ids if asset_id not in sprite_by_id)
        if path.name.startswith("LOCAL_"):
            catalog_level = None
            source = "local"
        else:
            catalog_level = int(path.name.split("_", 1)[0])
            source = "catalog"
        levels.append(
            {
                "file": path.name,
                "catalog_level": catalog_level,
                "source": source,
                "hash": level.get("hash"),
                "revision": level.get("revision"),
                "poster_title": level.get("poster_title"),
                "cgasset_ids": sorted(ids),
                "local_sprites": sorted(
                    name for asset_id in ids for name in sprite_by_id.get(asset_id, [])
                ),
                "missing_sprites": missing,
            }
        )

    data = {
        "entry_count": len(levels),
        "catalog_level_count": sum(1 for item in levels if item["source"] == "catalog"),
        "local_revision_count": sum(1 for item in levels if item["source"] == "local"),
        "unique_cgasset_ids": len(all_ids),
        "unique_local_sprites": len(sprite_by_id),
        "levels": levels,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
