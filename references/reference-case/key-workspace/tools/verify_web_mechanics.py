#!/usr/bin/env python3
"""Verify the recovered clue graph and obstacle state machine used by the web demo."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
OUTPUT = ROOT / "output"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def trigger_map(level: dict) -> dict[str, set[str]]:
    clues = {clue["id"] for clue in level["clues"]}
    triggers = {clue_id: set() for clue_id in clues}
    for item in level["items"]:
        for clue_id in item.get("connected_to", []):
            if clue_id not in clues:
                raise AssertionError(
                    f"{level.get('poster_title')}: {item['id']} references missing {clue_id}"
                )
            triggers[clue_id].add(item["id"])
    return triggers


def item_trigger_graph(level: dict) -> dict[str, list[str]]:
    return {item["id"]: item.get("connected_to", []) for item in level["items"]}


class LevelSimulation:
    def __init__(self, level: dict):
        self.level = level
        self.cells: dict[tuple[int, int], dict] = {}
        self.slots: list[dict] = []
        self.pending: set[int] = set()

        for item in level["items"]:
            for cell_data in item.get("cells", []):
                key = (cell_data["row"], cell_data["column"])
                self.cells.setdefault(
                    key,
                    {"curtain": 0, "lock_and_key": None, "unlocked": False},
                )
                self.slots.append(
                    {
                        "item_id": item["id"],
                        "row": cell_data["row"],
                        "column": cell_data["column"],
                        "revealed": False,
                    }
                )

        for cell_data in level.get("cells", []):
            key = (cell_data["row"], cell_data["column"])
            cell = self.cells.setdefault(
                key,
                {"curtain": 0, "lock_and_key": None, "unlocked": False},
            )
            cell["curtain"] = cell_data.get("lock", 0) or 0
            cell["lock_and_key"] = cell_data.get("lock_and_key")

        for item in level["items"]:
            if item.get("revealed"):
                self.reveal_item(item["id"])
        self.process_pending()

    def cell_for_slot(self, slot: dict) -> dict:
        return self.cells[(slot["row"], slot["column"])]

    def is_blocked(self, cell: dict) -> bool:
        if cell["curtain"] > 0:
            return True
        lock_and_key = cell["lock_and_key"]
        return bool(
            lock_and_key
            and lock_and_key.get("type") == "lock"
            and not cell["unlocked"]
        )

    def unlock(self, color: str) -> bool:
        changed = False
        for cell in self.cells.values():
            lock_and_key = cell["lock_and_key"]
            if (
                lock_and_key
                and lock_and_key.get("type") == "lock"
                and lock_and_key.get("color") == color
                and not cell["unlocked"]
            ):
                cell["unlocked"] = True
                changed = True
        return changed

    def reveal_slot(self, index: int) -> str | None:
        slot = self.slots[index]
        if slot["revealed"]:
            return None
        slot["revealed"] = True
        lock_and_key = self.cell_for_slot(slot)["lock_and_key"]
        if lock_and_key and lock_and_key.get("type") == "key":
            return lock_and_key.get("color")
        return None

    def reveal_item(self, item_id: str) -> int:
        colors = set()
        revealed_count = 0
        for index, slot in enumerate(self.slots):
            if slot["item_id"] != item_id or slot["revealed"]:
                continue
            if self.is_blocked(self.cell_for_slot(slot)):
                self.pending.add(index)
                continue
            color = self.reveal_slot(index)
            if color:
                colors.add(color)
            revealed_count += 1
        for color in colors:
            self.unlock(color)
        revealed_count += self.process_pending()
        return revealed_count

    def process_pending(self) -> int:
        changed = True
        revealed_count = 0
        while changed:
            changed = False
            colors = set()
            for index in list(self.pending):
                slot = self.slots[index]
                if self.is_blocked(self.cell_for_slot(slot)):
                    continue
                self.pending.remove(index)
                color = self.reveal_slot(index)
                if color:
                    colors.add(color)
                revealed_count += 1
                changed = True
            for color in colors:
                if self.unlock(color):
                    changed = True
        return revealed_count

    def decrement_curtains(self, amount: int) -> None:
        reveal_wave = amount
        while reveal_wave > 0:
            for cell in self.cells.values():
                cell["curtain"] = max(0, cell["curtain"] - reveal_wave)
            reveal_wave = self.process_pending()

    def item_fully_revealed(self, item_id: str) -> bool:
        slots = [slot for slot in self.slots if slot["item_id"] == item_id]
        return bool(slots) and all(slot["revealed"] for slot in slots)

    def run_to_completion(self) -> None:
        while not all(slot["revealed"] for slot in self.slots):
            candidate = next(
                (
                    item["id"]
                    for item in self.level["items"]
                    if not self.item_fully_revealed(item["id"])
                    and any(
                        slot["item_id"] == item["id"]
                        and not slot["revealed"]
                        and not self.is_blocked(self.cell_for_slot(slot))
                        for slot in self.slots
                    )
                ),
                None,
            )
            if candidate is None:
                remaining = sorted(
                    {slot["item_id"] for slot in self.slots if not slot["revealed"]}
                )
                raise AssertionError(
                    f"{self.level.get('poster_title')}: obstacle deadlock for {remaining}"
                )
            revealed_count = self.reveal_item(candidate)
            self.decrement_curtains(revealed_count)


def advance_clues(level: dict, revealed_items: set[str]) -> tuple[set[str], set[str]]:
    triggers = trigger_map(level)
    revealed_clues = {clue["id"] for clue in level["clues"] if clue.get("revealed")}
    completed_clues = set()
    for clue in level["clues"]:
        if triggers[clue["id"]] and triggers[clue["id"]] <= revealed_items:
            revealed_clues.add(clue["id"])
        connected = set(clue.get("connected_to", []))
        if clue["id"] in revealed_clues and connected and connected <= revealed_items:
            completed_clues.add(clue["id"])
    return revealed_clues, completed_clues


def verify_first_level_chain(level: dict) -> None:
    revealed_items: set[str] = set()
    revealed, _ = advance_clues(level, revealed_items)
    if revealed != {"clue-1", "clue-2"}:
        raise AssertionError(f"level 1 initial clues changed: {sorted(revealed)}")

    revealed_items.add("item-1")
    revealed, _ = advance_clues(level, revealed_items)
    if "clue-3" in revealed:
        raise AssertionError("level 1 clue-3 revealed before its trigger item")

    revealed_items.add("item-2")
    revealed, completed = advance_clues(level, revealed_items)
    if "clue-3" not in revealed or not {"clue-1", "clue-2"} <= completed:
        raise AssertionError("level 1 did not reveal clue-3 after the first clue pair")

    revealed_items.add("item-3")
    revealed, completed = advance_clues(level, revealed_items)
    if "clue-5" not in revealed or "clue-3" not in completed:
        raise AssertionError("level 1 did not reveal clue-5 after clue-3")


def main() -> None:
    manifest = load_json(WEB / "data" / "manifest.json")
    if len(manifest["levels"]) != 249:
        raise AssertionError(f"expected 249 web levels, found {len(manifest['levels'])}")

    optional_hidden_clues = 0
    obstacle_levels = 0
    for entry in manifest["levels"]:
        level = load_json(WEB / "levels" / entry["file"])
        triggers = trigger_map(level)
        optional_hidden_clues += sum(
            1
            for clue in level["clues"]
            if not clue.get("revealed") and not triggers[clue["id"]]
        )
        if level.get("cells"):
            obstacle_levels += 1
        LevelSimulation(level).run_to_completion()

    animal_manifest = load_json(WEB / "animal-data" / "manifest.json")
    if len(animal_manifest["levels"]) != 10:
        raise AssertionError("animal demo must contain levels 1-10")

    for entry in animal_manifest["levels"]:
        filename = entry["file"]
        animal = load_json(WEB / "animal-data" / "levels" / filename)
        source = load_json(WEB / "levels" / filename)
        if item_trigger_graph(animal) != item_trigger_graph(source):
            raise AssertionError(
                f"animal level {entry['catalogLevel']}: item trigger graph differs from source"
            )

    first_level = load_json(
        WEB / "animal-data" / "levels" / animal_manifest["levels"][0]["file"]
    )
    verify_first_level_chain(first_level)

    print("web levels checked: 249")
    print(f"obstacle state machines completed: {obstacle_levels}/{obstacle_levels}")
    print("animal item-to-clue trigger graphs preserved: 10/10")
    print("animal level 1 staged clue chain: passed")
    print(f"optional hidden clues without automatic triggers: {optional_hidden_clues}")


if __name__ == "__main__":
    main()
