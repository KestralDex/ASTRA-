from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "logs",
}

EXCLUDED_NAMES = {
    ".env",
}

EXCLUDED_SUFFIXES = {
    ".pyc",
    ".pyo",
}

# Raw/private data is intentionally excluded. Model artifacts are included.
RAW_DATA_MARKERS = {
    ("data", "raw"),
    ("archive",),
}


def should_exclude(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    parts = rel.parts

    if any(part in EXCLUDED_PARTS for part in parts):
        return True

    if path.name in EXCLUDED_NAMES:
        return True

    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return True

    for marker in RAW_DATA_MARKERS:
        if parts[: len(marker)] == marker:
            return True

    return False


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_dir = ROOT / "backups"
backup_dir.mkdir(exist_ok=True)

zip_path = backup_dir / f"ASTRA_demo_freeze_{timestamp}.zip"

files = [
    path
    for path in ROOT.rglob("*")
    if path.is_file()
    and not should_exclude(path)
    and "backups" not in path.relative_to(ROOT).parts
]

manifest = {
    "created_at_local": datetime.now().isoformat(timespec="seconds"),
    "project_root": str(ROOT),
    "raw_data_included": False,
    "environment_included": False,
    "files": {},
}

with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(files):
        rel = path.relative_to(ROOT)
        archive.write(path, rel)
        manifest["files"][str(rel)] = {
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
        }

    archive.writestr(
        "BACKUP_MANIFEST.json",
        json.dumps(manifest, indent=2),
    )

print(f"Created: {zip_path}")
print(f"Files included: {len(files)}")
print("Raw datasets, .env, .venv, Git metadata and caches were excluded.")
