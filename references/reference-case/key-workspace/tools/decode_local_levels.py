#!/usr/bin/env python3
"""Decode the pseudo-UTF8 obfuscation layer of local Griddle level assets."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


TEXT_RE = re.compile(r"^([0-9A-F]{32}_\d+)__(-?\d+)\.bin$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--configs", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("output/levels-encrypted"))
    return parser.parse_args()


def decode(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(data):
        if i + 2 < len(data) and data[i] == 0xED and data[i + 1] in (0xB2, 0xB3):
            value = data[i + 2] - 0x80
            if data[i + 1] == 0xB3:
                value += 0x40
            out.append(value)
            i += 3
        else:
            out.append(data[i])
            i += 1
    return bytes(out)


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    results = []
    for path in sorted((args.configs / "levels").glob("*.bin")):
        match = TEXT_RE.match(path.name)
        if not match:
            continue
        key, path_id = match.groups()
        raw = path.read_bytes()
        decoded = decode(raw)
        destination = args.output / f"{key}.bin"
        destination.write_bytes(decoded)
        results.append((key, path_id, len(raw), len(decoded)))
    report_path = args.output / "_decode-report.txt"
    report_path.write_text(
        "\n".join(f"{key}\t{path_id}\t{raw}\t{decoded}" for key, path_id, raw, decoded in results) + "\n"
    )
    print(f"decoded={len(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
