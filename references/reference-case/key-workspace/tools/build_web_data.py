#!/usr/bin/env python3
"""Build the static web app data set from recovered Griddle files."""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"
WEB = ROOT / "web"


def main() -> None:
    inventory = json.loads((OUTPUT / "level-inventory.json").read_text())
    assets = json.loads((OUTPUT / "assets-index.json").read_text())
    saga = json.loads(
        next((OUTPUT / "unity-extract" / "text").glob("Griddle_SagaLevels_*.json")).read_text()
    )

    assets_by_hash = {entry["hash"]: entry for entry in assets["levels"]}
    file_by_key = {
        f"{entry['hash']}_{entry['revision']}": entry["file"]
        for entry in assets["levels"]
    }
    saga_by_index = {int(k): v for k, v in saga["levels"].items()}

    levels = []
    for entry in inventory["entries"]:
        key = entry["key"]
        level_file = OUTPUT / "levels" / file_by_key[key]
        if not level_file.exists():
            raise FileNotFoundError(f"Missing level JSON: {level_file}")

        data = json.loads(level_file.read_text())
        asset_entry = assets_by_hash.get(entry["level_hash"])
        sprites = {}
        if asset_entry:
            sprites = dict(zip(asset_entry["cgasset_ids"], asset_entry["local_sprites"]))

        catalog_level = entry.get("catalog_level")
        saga_entry = saga_by_index.get(catalog_level) if catalog_level else None
        grid = data.get("grid", {})
        cells = data.get("cells", [])

        levels.append(
            {
                "file": file_by_key[key],
                "key": key,
                "catalogLevel": catalog_level,
                "source": "catalog" if catalog_level else "local",
                "posterTitle": data.get("poster_title", ""),
                "width": grid.get("width"),
                "height": grid.get("height"),
                "itemCount": len(data.get("items", [])),
                "clueCount": len(data.get("clues", [])),
                "slotCount": sum(len(item.get("cells", [])) for item in data.get("items", [])),
                "hasCurtain": any(isinstance(cell.get("lock"), int) and cell.get("lock", 0) > 0 for cell in cells),
                "hasLockKey": any(cell.get("lock_and_key") for cell in cells),
                "difficulty": (saga_entry or {}).get("difficulty"),
                "tutorialType": (saga_entry or {}).get("tutorial_type"),
                "isUsableInLoop": (saga_entry or {}).get("is_usable_in_loop"),
                "sprites": sprites,
            }
        )

    levels.sort(
        key=lambda level: (
            level["source"] != "catalog",
            level["catalogLevel"] if level["catalogLevel"] is not None else 10**9,
            level["file"],
        )
    )

    manifest = {
        "generatedAt": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "app": "Griddle Web",
        "source": "recovered Griddle level JSON + Unity sprites",
        "levels": levels,
    }

    web_data = WEB / "data"
    web_levels = WEB / "levels"
    web_data.mkdir(parents=True, exist_ok=True)
    web_levels.mkdir(parents=True, exist_ok=True)

    (web_data / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    for source in sorted((OUTPUT / "levels").glob("*.json")):
        level = json.loads(source.read_text())
        clue_ids = {clue["id"] for clue in level.get("clues", [])}
        for item in level.get("items", []):
            item["connected_to"] = [
                clue_id
                for clue_id in item.get("connected_to", [])
                if clue_id in clue_ids
            ]
        (web_levels / source.name).write_text(
            json.dumps(level, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    print(f"manifest levels: {len(levels)}")
    print(f"web levels copied: {len(list(web_levels.glob('*.json')))}")


if __name__ == "__main__":
    main()
