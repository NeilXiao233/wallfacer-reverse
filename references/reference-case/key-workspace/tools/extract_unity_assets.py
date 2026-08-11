#!/usr/bin/env python3
"""Extract recoverable Unity assets from an extracted iOS app bundle.

The tool scans the app's Data directory for UnityFS/asset files, exports
images, audio, text assets, and structured objects, and writes a manifest with
hashes and source references. It intentionally reports per-object failures
instead of aborting the whole extraction.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any

import UnityPy


IMAGE_TYPES = {"Texture2D", "Sprite"}
AUDIO_TYPES = {"AudioClip"}
TEXT_TYPES = {"TextAsset"}
STRUCTURED_TYPES = {
    "MonoBehaviour",
    "Material",
    "Shader",
    "Mesh",
    "AnimationClip",
    "AnimatorController",
    "VideoClip",
    "Font",
}
INTERESTING_TERMS = (
    "level",
    "config",
    "data",
    "setting",
    "local",
    "word",
    "grid",
    "theme",
    "translation",
)
SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")
JSON_EXTENSIONS = {".json", ".txt", ".xml", ".csv", ".tsv", ".yaml", ".yml"}


def safe_name(value: str, fallback: str = "unnamed") -> str:
    cleaned = SAFE_NAME.sub("_", str(value).strip()).strip("._")
    return cleaned[:180] or fallback


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_safe(value: Any, depth: int = 0) -> Any:
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return value.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
    if isinstance(value, bytes):
        return {
            "byte_length": len(value),
            "preview_hex": value[:64].hex(),
        }
    if isinstance(value, dict):
        return {str(key): json_safe(item, depth + 1) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item, depth + 1) for item in value]
    if hasattr(value, "path_id"):
        return {"path_id": value.path_id}
    if depth > 4:
        return repr(value)[:200]
    return repr(value)


def unique_path(directory: Path, name: str, suffix: str, path_id: int) -> Path:
    return directory / f"{name}__{path_id}{suffix}"


def discover_asset_files(app: Path) -> list[Path]:
    data = app / "Data"
    if not data.is_dir():
        raise SystemExit(f"Missing Unity Data directory: {data}")
    candidates: list[Path] = []
    for path in data.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in {".assets", ".bundle", ".unity3d", ".resource", ".asset"}:
            candidates.append(path)
    for extra in ("globalgamemanagers", "globalgamemanagers.assets"):
        path = data / extra
        if path.is_file() and path not in candidates:
            candidates.append(path)
    return sorted(candidates, key=lambda path: str(path))


def export_text_asset(data: Any, output: Path, path_id: int, source: Path, root: Path) -> dict[str, Any]:
    name = safe_name(getattr(data, "m_Name", ""), f"text_{path_id}")
    script = getattr(data, "m_Script", b"")
    if isinstance(script, str):
        raw = script.encode("utf-8", errors="replace")
    else:
        raw = bytes(script or b"")
    suffix = ".bin"
    try:
        text = raw.decode("utf-8")
        suffix = ".txt"
        stripped = text.lstrip()
        if stripped.startswith(("{", "[")):
            try:
                json.loads(text)
                suffix = ".json"
            except Exception:
                pass
        elif stripped[:200].lower().lstrip().startswith(("<xml", "<?xml")):
            suffix = ".xml"
    except Exception:
        text = None
    destination = unique_path(output / "text", name, suffix, path_id)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(raw)
    preview = text[:200] if text is not None else None
    if isinstance(preview, str):
        preview = preview.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
    return {
        "destination": destination.relative_to(root).as_posix(),
        "bytes": destination.stat().st_size,
        "sha256": sha256_path(destination),
        "preview": preview,
    }


def export_structured_object(
    obj: Any,
    data: Any,
    type_name: str,
    output: Path,
    path_id: int,
    source: Path,
    root: Path,
) -> dict[str, Any] | None:
    name = safe_name(getattr(data, "m_Name", ""), f"{type_name}_{path_id}")
    if not any(term in name.lower() for term in INTERESTING_TERMS):
        return None
    try:
        tree = obj.read_typetree()
        payload = json_safe(tree)
        suffix = ".json"
    except Exception:
        payload = None
        suffix = ".bin"
    if payload is None:
        try:
            raw = data.raw_data if hasattr(data, "raw_data") else b""
            payload = {"raw_hex": bytes(raw[:128]).hex(), "raw_length": len(raw)}
        except Exception:
            payload = {}
    destination = unique_path(output / "objects" / safe_name(type_name), name, suffix, path_id)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if suffix == ".json":
        destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        destination.write_bytes(b"")
    return {
        "destination": destination.relative_to(root).as_posix(),
        "bytes": destination.stat().st_size,
        "sha256": sha256_path(destination),
    }


def export_object(
    obj: Any,
    source: Path,
    output: Path,
    root: Path,
    records: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    options: argparse.Namespace,
) -> None:
    type_name = obj.type.name
    path_id = obj.path_id
    row: dict[str, Any] = {
        "source": source.relative_to(root).as_posix(),
        "type": type_name,
        "path_id": path_id,
    }
    try:
        data = obj.read()
        row["name"] = str(getattr(data, "m_Name", ""))
    except Exception as error:
        failures.append(
            {
                "source": source.relative_to(root).as_posix(),
                "type": type_name,
                "path_id": path_id,
                "error": f"{type(error).__name__}: {error}",
            }
        )
        return

    exported: dict[str, Any] | None = None
    try:
        if type_name in IMAGE_TYPES:
            name = safe_name(getattr(data, "m_Name", ""), f"{type_name}_{path_id}")
            if type_name == "Texture2D" and (getattr(data, "m_Width", 0) == 0 or getattr(data, "m_Height", 0) == 0):
                row["skipped"] = "zero-sized texture"
                records.append(row)
                return
            image = getattr(data, "image", None)
            if image is None:
                row["skipped"] = "no decodable image payload"
                records.append(row)
                return
            directory = output / "assets/images" / ("sprites" if type_name == "Sprite" else "textures")
            directory.mkdir(parents=True, exist_ok=True)
            destination = unique_path(directory, name, ".png", path_id)
            image.save(destination)
            exported = {
                "destination": destination.relative_to(root).as_posix(),
                "bytes": destination.stat().st_size,
                "sha256": sha256_path(destination),
                "width": getattr(data, "m_Width", None),
                "height": getattr(data, "m_Height", None),
            }
        elif type_name in AUDIO_TYPES:
            name = safe_name(getattr(data, "m_Name", ""), f"audio_{path_id}")
            directory = output / "assets/audio"
            directory.mkdir(parents=True, exist_ok=True)
            exported_files = []
            for sample_name, payload in data.samples.items():
                sample_path = Path(sample_name)
                suffix = sample_path.suffix.lower() or ".bin"
                destination = unique_path(directory, safe_name(sample_path.stem, name), suffix, path_id)
                destination.write_bytes(payload)
                exported_files.append(
                    {
                        "destination": destination.relative_to(root).as_posix(),
                        "bytes": destination.stat().st_size,
                        "sha256": sha256_path(destination),
                    }
                )
            exported = {"files": exported_files}
        elif type_name in TEXT_TYPES:
            exported = export_text_asset(data, output, path_id, source, root)
        elif type_name in STRUCTURED_TYPES:
            exported = export_structured_object(obj, data, type_name, output, path_id, source, root)
            if exported is None:
                records.append(row)
                return
    except Exception as error:
        failures.append(
            {
                "source": source.relative_to(root).as_posix(),
                "type": type_name,
                "path_id": path_id,
                "name": row.get("name", ""),
                "error": f"{type(error).__name__}: {error}",
            }
        )
        return

    if exported is not None:
        row["exported"] = exported
    records.append(row)


def process_file(
    source: Path,
    output: Path,
    root: Path,
    records: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    options: argparse.Namespace,
) -> tuple[int, Counter[str]]:
    environment = UnityPy.load(str(source))
    counts: Counter[str] = Counter()
    exported_count = 0
    for obj in environment.objects:
        counts[obj.type.name] += 1
        before = len(records)
        export_object(obj, source, output, root, records, failures, options)
        if len(records) > before:
            exported_count += 1
    return exported_count, counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", type=Path, required=True, help="Extracted Griddle.app directory")
    parser.add_argument("--output", type=Path, default=Path("output/unity-extract"))
    args = parser.parse_args()

    app = args.app.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    root = Path(os.path.commonpath([str(app), str(output)]))
    records: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    source_counts: dict[str, Counter[str]] = {}
    total_objects = 0
    total_exported = 0

    for source in discover_asset_files(app):
        try:
            exported, counts = process_file(source, output, root, records, failures, args)
            source_counts[source.relative_to(app).as_posix()] = dict(counts.most_common())
            total_objects += sum(counts.values())
            total_exported += exported
        except Exception as error:
            failures.append(
                {
                    "source": source.relative_to(app).as_posix(),
                    "error": f"{type(error).__name__}: {error}",
                }
            )

    summary = {
        "app": str(app),
        "asset_file_count": len(source_counts),
        "object_count": total_objects,
        "record_count": len(records),
        "exported_count": total_exported,
        "failure_count": len(failures),
        "object_type_counts": {
            source: counts for source, counts in source_counts.items()
        },
    }
    manifest = {
        "summary": summary,
        "records": records,
        "failures": failures,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
