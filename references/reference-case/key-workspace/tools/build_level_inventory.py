#!/usr/bin/env python3
"""Build a unified inventory of Griddle level revisions.

The saga catalog only names 214 active levels, while the IPA contains 249
local level revisions (configs and asset bundles). This inventory merges both
so every locally present revision can be checked against the Cheer CDN.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


TEXT_RE = re.compile(r"^([0-9A-F]{32})_(\d+)__(-?\d+)\.bin$")
BUNDLE_RE = re.compile(
    r"^levelassets_([0-9a-f]{32})_(\d+)_assets_all_([0-9a-f]{32})\.bundle$"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--configs", type=Path, required=True)
    parser.add_argument("--app", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("output/level-inventory.json"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
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
                "bundle_files": [],
            },
        )
        entry["config_files"].append(path.name)

    for path in (args.app / "Data" / "Raw" / "aa" / "iOS").iterdir():
        match = BUNDLE_RE.match(path.name)
        if not match:
            continue
        level_hash, revision, _ = match.groups()
        key = f"{level_hash.upper()}_{revision}"
        entry = entries.setdefault(
            key,
            {
                "key": key,
                "level_hash": level_hash.upper(),
                "revision": int(revision),
                "catalog_level": level_by_key.get(key),
                "config_files": [],
                "bundle_files": [],
            },
        )
        entry["bundle_files"].append(f"Data/Raw/aa/iOS/{path.name}")

    data = {
        "entry_count": len(entries),
        "catalog_level_count": sum(1 for entry in entries.values() if entry["catalog_level"] is not None),
        "local_only_count": sum(1 for entry in entries.values() if entry["catalog_level"] is None),
        "entries": sorted(entries.values(), key=lambda item: (item["catalog_level"] is None, item["catalog_level"] or 0, item["revision"])),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
