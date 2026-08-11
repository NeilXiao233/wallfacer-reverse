#!/usr/bin/env python3
"""Build a level map from Griddle bundle names and exported Unity assets."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


BUNDLE_RE = re.compile(
    r"^levelassets_([0-9a-f]{32})_(\d+)_assets_all_([0-9a-f]{32})\.bundle$"
)
TEXT_RE = re.compile(r"^([0-9A-F]{32})_(\d+)__(-?\d+)\.bin$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", type=Path, required=True)
    parser.add_argument("--configs", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("output/level-map.json"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    app = args.app.resolve()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    with args.catalog.open() as handle:
        catalog = json.load(handle)
    level_by_key = {
        info["key"]: int(level) for level, info in catalog["levels"].items()
    }

    entries: dict[str, dict[str, object]] = {}
    for path in (args.configs / "levels").iterdir():
        match = TEXT_RE.match(path.name)
        if not match:
            continue
        level_hash, revision, _ = match.groups()
        key = f"{level_hash}_{revision}"
        entry = entries.setdefault(
            key,
            {
                "key": key,
                "level_hash": level_hash,
                "revision": int(revision),
                "catalog_level": level_by_key.get(key),
                "config_files": [],
                "bundle_file": None,
                "bundle_hash": None,
                "assets": [],
            },
        )
        entry["config_files"].append(path.name)

    for path in (app / "Data" / "Raw" / "aa" / "iOS").iterdir():
        match = BUNDLE_RE.match(path.name)
        if not match:
            continue
        level_hash, revision, bundle_hash = match.groups()
        key = f"{level_hash.upper()}_{revision}"
        entry = entries.setdefault(
            key,
            {
                "key": key,
                "level_hash": level_hash.upper(),
                "revision": int(revision),
                "catalog_level": level_by_key.get(key),
                "config_files": [],
                "bundle_file": None,
                "bundle_hash": None,
                "assets": [],
            },
        )
        entry["bundle_file"] = f"Data/Raw/aa/iOS/{path.name}"
        entry["bundle_hash"] = bundle_hash

    with args.manifest.open() as handle:
        manifest = json.load(handle)
    assets_by_source: dict[str, list[dict[str, object]]] = defaultdict(list)
    for record in manifest["records"]:
        if record["type"] not in {"Sprite", "Texture2D"} or "exported" not in record:
            continue
        assets_by_source[record["source"]].append(
            {
                "type": record["type"],
                "name": record.get("name", ""),
                "path_id": record["path_id"],
                "destination": record["exported"]["destination"],
            }
        )

    for entry in entries.values():
        bundle_file = entry["bundle_file"]
        if bundle_file:
            entry["assets"] = assets_by_source.get(
                f"device/ipa-extracted/Payload/Griddle.app/{bundle_file}", []
            )
        entry["config_files"] = sorted(entry["config_files"])
    levels = sorted(
        entries.values(),
        key=lambda item: (item["catalog_level"] is None, item["catalog_level"] or 0, item["revision"]),
    )

    data = {
        "revision_count": len(levels),
        "bundle_count": sum(1 for item in levels if item["bundle_file"]),
        "config_text_count": sum(len(item["config_files"]) for item in levels),
        "catalog_level_matches": sum(1 for item in levels if item["catalog_level"] is not None),
        "levels": levels,
    }
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
