#!/usr/bin/env python3
"""Verify the Griddle recovery outputs against each other."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("output/recovery-verification.json"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.workspace.resolve()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    checks: dict[str, object] = {}
    failures: list[str] = []

    report_path = root / "output" / "levels" / "_download-report.txt"
    report_lines = report_path.read_text().splitlines()
    failed_downloads = [line for line in report_lines if "\t" in line and line.split("\t")[1] != "ok"]
    checks["download_report_ok"] = len(failed_downloads) == 0
    if failed_downloads:
        failures.append(f"failed downloads: {len(failed_downloads)}")

    level_files = sorted(
        path for path in (root / "output" / "levels").glob("*.json") if path.name != "_download-report.txt"
    )
    bad_json: list[str] = []
    bad_key: list[str] = []
    for path in level_files:
        try:
            with path.open() as handle:
                data = json.load(handle)
        except Exception as error:
            bad_json.append(f"{path.name}: {error}")
            continue
        expected_key = path.stem
        if path.name.startswith("LOCAL_"):
            expected_key = path.stem.removeprefix("LOCAL_")
        else:
            expected_key = "_".join(path.stem.split("_")[1:])
        actual_key = f"{data.get('hash')}_{data.get('revision')}"
        if actual_key != expected_key:
            bad_key.append(f"{path.name}: expected {expected_key}, got {actual_key}")
    checks["level_json_parse"] = not bad_json
    checks["level_json_key_match"] = not bad_key
    failures.extend(bad_json)
    failures.extend(bad_key)

    with (root / "output" / "assets-index.json").open() as handle:
        asset_index = json.load(handle)
    missing = sum(len(item["missing_sprites"]) for item in asset_index["levels"])
    checks["missing_sprite_references"] = missing
    if missing:
        failures.append(f"{missing} sprite references missing")

    with (root / "output" / "level-map.json").open() as handle:
        level_map = json.load(handle)
    missing_bundle = [
        item["key"]
        for item in level_map["levels"]
        if item["bundle_file"]
        and not (root / "device" / "ipa-extracted" / "Payload" / "Griddle.app" / item["bundle_file"]).exists()
    ]
    checks["level_map_bundle_files_exist"] = not missing_bundle
    if missing_bundle:
        failures.append(f"missing bundle files: {missing_bundle[:5]}")

    decoded_path = root / "output" / "levels-encrypted"
    decoded_count = len(list(decoded_path.glob("*.bin")))
    checks["decoded_local_level_count"] = decoded_count
    if decoded_count != level_map["revision_count"]:
        failures.append(f"decoded local levels {decoded_count} != revisions {level_map['revision_count']}")

    with (root / "output" / "unity-extract" / "manifest.json").open() as handle:
        manifest = json.load(handle)
    missing_dest = [
        record["exported"]["destination"]
        for record in manifest["records"]
        if "exported" in record and not (root / record["exported"]["destination"]).exists()
    ]
    checks["manifest_destinations_exist"] = not missing_dest
    if missing_dest:
        failures.append(f"manifest destinations missing: {len(missing_dest)}")

    checks["all_checks_passed"] = not failures
    report = {
        "checks": checks,
        "level_json_count": len(level_files),
        "failures": failures,
    }
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
