#!/usr/bin/env python3
"""Verify animal levels preserve recovered logic while replacing all gameplay semantics."""

from __future__ import annotations

import argparse
import itertools
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"
WEB = ROOT / "web"
ANIMAL_DATA = WEB / "animal-data"
ANIMAL_AVATARS = WEB / "assets" / "animal" / "cast"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"not a PNG: {path}")
    return struct.unpack(">II", data[16:24])


def comparable_cells(items: list[dict]) -> dict[str, list[dict]]:
    return {item["id"]: item.get("cells", []) for item in items}


def comparable_item_triggers(items: list[dict]) -> dict[str, list[str]]:
    return {item["id"]: item.get("connected_to", []) for item in items}


def comparable_clues(clues: list[dict]) -> list[dict]:
    return [
        {
            "id": clue["id"],
            "connected_to": clue.get("connected_to", []),
            "revealed": clue.get("revealed", False),
            "is_hard": clue.get("is_hard", False),
        }
        for clue in clues
    ]


def item_column(assignment: dict[str, int], item_id: str) -> int:
    return assignment[item_id]


def subject_column(assignment: dict[str, int], subject: dict) -> int:
    if "item" in subject:
        return item_column(assignment, subject["item"])
    return subject["column"]


def value_at_column(assignment: dict[str, int], column: int, value_items: dict[str, int]) -> int:
    matches = [value for item_id, value in value_items.items() if assignment[item_id] == column]
    if len(matches) != 1:
        raise AssertionError(f"expected one value item at column {column}, found {len(matches)}")
    return matches[0]


def constraint_matches(assignment: dict[str, int], constraint: dict) -> bool:
    kind = constraint["type"]
    if kind == "assign":
        return item_column(assignment, constraint["item"]) == constraint["column"]
    if kind == "not_assign":
        return item_column(assignment, constraint["item"]) != constraint["column"]
    if kind == "same":
        first, second = constraint["items"]
        return item_column(assignment, first) == item_column(assignment, second)
    if kind == "not_same":
        first, second = constraint["items"]
        return item_column(assignment, first) != item_column(assignment, second)
    if kind == "adjacent":
        first, second = constraint["items"]
        return abs(item_column(assignment, first) - item_column(assignment, second)) == 1
    if kind == "not_adjacent":
        first, second = constraint["items"]
        return abs(item_column(assignment, first) - item_column(assignment, second)) != 1
    if kind in {"value_delta", "value_ratio"}:
        first, second = constraint["subjects"]
        first_value = value_at_column(
            assignment,
            subject_column(assignment, first),
            constraint["value_items"],
        )
        second_value = value_at_column(
            assignment,
            subject_column(assignment, second),
            constraint["value_items"],
        )
        if kind == "value_delta":
            return first_value - second_value == constraint["delta"]
        return (
            first_value * constraint["denominator"]
            == second_value * constraint["numerator"]
        )
    raise AssertionError(f"unknown constraint type: {kind}")


def solve_level(level: dict, clue_constraints: dict) -> list[dict[str, int]]:
    width = level["grid"]["width"]
    row_items: dict[int, list[str]] = {}
    for item in level["items"]:
        rows = {cell["row"] for cell in item.get("cells", [])}
        if len(rows) != 1:
            raise AssertionError(f"solver expects each item in one row: {item['id']}")
        row_items.setdefault(rows.pop(), []).append(item["id"])

    row_assignments = []
    for row in range(1, level["grid"]["height"] + 1):
        items = row_items[row]
        if len(items) != width:
            raise AssertionError(f"row {row} has {len(items)} items for width {width}")
        row_assignments.append(
            [dict(zip(items, permutation)) for permutation in itertools.permutations(range(1, width + 1))]
        )

    constraints = [
        constraint
        for clue_id in [clue["id"] for clue in level["clues"]]
        for constraint in clue_constraints[clue_id]
    ]
    solutions = []
    for combination in itertools.product(*row_assignments):
        assignment = {}
        for row_assignment in combination:
            assignment.update(row_assignment)
        if all(constraint_matches(assignment, constraint) for constraint in constraints):
            solutions.append(assignment)
    return solutions


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-assets", action="store_true")
    args = parser.parse_args()

    manifest = load_json(ANIMAL_DATA / "manifest.json")
    logic_model = load_json(OUTPUT / "animal" / "logic-model.json")
    inventory = load_json(OUTPUT / "level-inventory.json")
    assets_index = load_json(OUTPUT / "assets-index.json")
    if len(manifest["levels"]) != 10:
        raise AssertionError(f"animal manifest must contain 10 levels, got {len(manifest['levels'])}")
    if [entry["catalogLevel"] for entry in manifest["levels"]] != list(range(1, 11)):
        raise AssertionError("animal manifest must contain catalog levels 1 through 10 in order")

    file_by_key = {
        f"{entry['hash']}_{entry['revision']}": entry["file"]
        for entry in assets_index["levels"]
    }
    inventory_by_level = {
        entry["catalog_level"]: entry
        for entry in inventory["entries"]
        if entry.get("catalog_level") and 1 <= entry["catalog_level"] <= 10
    }

    checked_assets = 0
    checked_avatar_indices = set()
    unique_solutions = 0
    preserved_trigger_graphs = 0
    for manifest_entry in manifest["levels"]:
        catalog_level = manifest_entry["catalogLevel"]
        filename = manifest_entry["file"]
        source_entry = inventory_by_level[catalog_level]
        source = load_json(OUTPUT / "levels" / file_by_key[source_entry["key"]])
        animal = load_json(ANIMAL_DATA / "levels" / filename)

        if (animal["grid"]["width"], animal["grid"]["height"]) != (
            source["grid"]["width"],
            source["grid"]["height"],
        ):
            raise AssertionError(f"level {catalog_level}: grid dimensions changed")
        if comparable_cells(animal["items"]) != comparable_cells(source["items"]):
            raise AssertionError(f"level {catalog_level}: answer cell mapping changed")
        if comparable_item_triggers(animal["items"]) != comparable_item_triggers(source["items"]):
            raise AssertionError(f"level {catalog_level}: item-to-clue trigger graph changed")
        preserved_trigger_graphs += 1
        if comparable_clues(animal["clues"]) != comparable_clues(source["clues"]):
            raise AssertionError(f"level {catalog_level}: clue unlock graph changed")
        if (animal.get("cells") or []) != (source.get("cells") or []):
            raise AssertionError(f"level {catalog_level}: lock/curtain cell metadata changed")

        clue_constraints = logic_model["levels"][str(catalog_level)]
        animal_clue_ids = [clue["id"] for clue in animal["clues"]]
        if set(clue_constraints) != set(animal_clue_ids):
            raise AssertionError(f"level {catalog_level}: executable constraints do not cover every clue")
        solutions = solve_level(animal, clue_constraints)
        if len(solutions) != 1:
            raise AssertionError(
                f"level {catalog_level}: directed clues yield {len(solutions)} solutions instead of 1"
            )
        source_solution = {
            item["id"]: item["cells"][0]["column"]
            for item in source["items"]
        }
        if solutions[0] != source_solution:
            raise AssertionError(f"level {catalog_level}: unique solution differs from recovered source")
        unique_solutions += 1

        for item in animal["items"]:
            if item.get("image_cgasset_id"):
                raise AssertionError(f"level {catalog_level}: original item art leaked into animal data")
            asset = item.get("animal_asset")
            if not asset:
                raise AssertionError(f"level {catalog_level}: {item['id']} has no animal asset mapping")
            if asset.get("columns") != 4 or asset.get("rows") != 4:
                raise AssertionError(f"level {catalog_level}: item sheet must remain a 4x4 grid")

        if args.require_assets:
            sheet = WEB / manifest_entry["itemSheet"]
            if not sheet.exists():
                raise AssertionError(f"level {catalog_level}: missing item sheet {sheet}")
            if png_dimensions(sheet) != (1024, 1024):
                raise AssertionError(f"level {catalog_level}: item sheet is not 1024x1024")
            checked_assets += 1
            for column in animal["grid"]["columns"]:
                avatar_index = column["animal_index"]
                avatar = ANIMAL_AVATARS / f"avatar-{avatar_index:02d}.webp"
                if not avatar.exists():
                    raise AssertionError(f"level {catalog_level}: missing animal avatar {avatar}")
                header = avatar.read_bytes()[:12]
                if header[:4] != b"RIFF" or header[8:12] != b"WEBP":
                    raise AssertionError(f"level {catalog_level}: invalid WebP avatar {avatar}")
                checked_avatar_indices.add(avatar_index)

    print("animal levels: 10")
    print("answer cell mappings preserved: 10/10")
    print(f"item-to-clue trigger graphs preserved: {preserved_trigger_graphs}/10")
    print("clue unlock graphs preserved: 10/10")
    print(f"executable unique solutions matching source: {unique_solutions}/10")
    print("original item art references: 0")
    if args.require_assets:
        print(f"1024x1024 item sheets: {checked_assets}/10")
        print(f"clean animal avatars: {len(checked_avatar_indices)}")


if __name__ == "__main__":
    main()
