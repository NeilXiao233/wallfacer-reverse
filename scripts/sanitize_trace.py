#!/usr/bin/env python3
"""Create a portable, reviewable transcript without embedded secrets or local identifiers."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

PATTERNS = (
    (re.compile(r"data:(?:image|audio|video)/[^,;]+(?:;base64)?,[^\"'\s]+", re.I), "[OMITTED_EMBEDDED_MEDIA]"),
    (re.compile(r"/Users/[^/\\\"'\s]+"), "/Users/REDACTED"),
    (re.compile(r"[A-Za-z0-9_-]*xiaozh[A-Za-z0-9_-]*", re.I), "REDACTED_USER"),
    (re.compile(r"(?<![0-9A-Fa-f])(?:[0-9A-Fa-f]{8}-[0-9A-Fa-f]{16,24})(?![0-9A-Fa-f])"), "[REDACTED_DEVICE_ID]"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
    (re.compile(r"(?i)(authorization\s*[:=]\s*(?:bearer\s+)?)[^\\\"'\s,;]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(cookie\s*[:=]\s*)[^\\\"'\r\n]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(--(?:password|token|api[-_]?key|secret)\s+)[^\s]+"), r"\1[REDACTED]"),
)
KEYS = {"password", "passwd", "authorization", "cookie", "token", "access_token", "refresh_token", "api_key", "secret"}

def clean_text(value: str) -> str:
    for regex, replacement in PATTERNS:
        value = regex.sub(replacement, value)
    return value

def clean(value, key: str | None = None):
    if key and key.lower() in KEYS and isinstance(value, str):
        return "[REDACTED]"
    if isinstance(value, str):
        return clean_text(value)
    if isinstance(value, list):
        return [clean(item) for item in value]
    if isinstance(value, dict):
        return {clean_text(str(k)): clean(v, str(k)) for k, v in value.items()}
    return value

def keep_record(item):
    """Drop global prompt/world-state envelopes that would import unrelated projects."""
    kind = item.get("type")
    if kind == "session_meta":
        payload = item.get("payload", {})
        return {"type": "session_meta", "payload": {"id": payload.get("id"), "timestamp": payload.get("timestamp")}}
    if kind == "event_msg":
        return item
    if kind == "response_item":
        payload = item.get("payload", {})
        if payload.get("type") == "message" and payload.get("role") == "developer":
            return None
        return item
    return None

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("destination", type=Path)
    ap.add_argument("--redact", action="append", default=[], help="literal text to remove from a portable trace")
    ns = ap.parse_args()
    total = 0
    with ns.source.open() as src, ns.destination.open("w") as dst:
        for number, line in enumerate(src, 1):
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"line {number}: invalid JSONL: {exc}")
            item = keep_record(item)
            if item is not None:
                item = clean(item)
                encoded = json.dumps(item, ensure_ascii=True, separators=(",", ":"))
                for term in ns.redact:
                    encoded = encoded.replace(term, "[OMITTED_OTHER_PROJECT]")
                dst.write(encoded + "\n")
                total += 1
    print(f"sanitized {total} records")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
