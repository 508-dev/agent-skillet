"""Manage the project lock file at ``.skillet/skillet.lock``."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

LOCK_VERSION = 1
LOCK_REL_PATH = Path(".skillet") / "skillet.lock"


def lock_path(project_dir: Path) -> Path:
    """Absolute path to this project's skillet lock file."""
    return project_dir / LOCK_REL_PATH


def _empty_lock() -> dict:
    return {"version": LOCK_VERSION, "skills": {}}


def _normalize_entry(raw: object) -> dict:
    if not isinstance(raw, dict):
        return {"origin": "", "mirrors": []}
    origin = raw.get("origin")
    mirrors = raw.get("mirrors")
    if not isinstance(origin, str):
        origin = ""
    if not isinstance(mirrors, list):
        mirrors = []
    clean_mirrors = [m for m in mirrors if isinstance(m, str) and m.strip()]
    return {"origin": origin, "mirrors": clean_mirrors}


def _normalized_lock(raw: object) -> dict:
    if not isinstance(raw, dict):
        return _empty_lock()
    raw_skills = raw.get("skills")
    skills: dict[str, dict] = {}
    if isinstance(raw_skills, dict):
        for name, value in raw_skills.items():
            if isinstance(name, str) and name.strip():
                skills[name] = _normalize_entry(value)
    return {"version": LOCK_VERSION, "skills": skills}


def load_lock(project_dir: Path) -> dict:
    """Load lock JSON; invalid or missing files return an empty lock shape."""
    path = lock_path(project_dir)
    if not path.exists():
        return _empty_lock()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_lock()
    return _normalized_lock(raw)


def save_lock(project_dir: Path, payload: dict) -> None:
    """Persist lock JSON with canonical shape."""
    path = lock_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = _normalized_lock(payload)
    path.write_text(json.dumps(normalized, indent=2), encoding="utf-8")


def is_managed(project_dir: Path, skill_name: str) -> bool:
    """Whether ``skill_name`` is managed by Skillet according to the lock."""
    return skill_name in load_lock(project_dir).get("skills", {})


def record_skill(
    project_dir: Path,
    skill_name: str,
    *,
    origin: str,
    mirrors: list[str] | None = None,
) -> None:
    """Create/update a lock entry for one skill."""
    lock = load_lock(project_dir)
    lock["skills"][skill_name] = {
        "origin": origin.strip(),
        "mirrors": [m for m in (mirrors or []) if isinstance(m, str) and m.strip()],
    }
    save_lock(project_dir, lock)


def unrecord_skill(project_dir: Path, skill_name: str) -> list[Path]:
    """Remove one lock entry and delete any mirrored files/directories it listed."""
    lock = load_lock(project_dir)
    entry = lock["skills"].pop(skill_name, None)
    save_lock(project_dir, lock)

    removed: list[Path] = []
    if not isinstance(entry, dict):
        return removed

    mirrors = entry.get("mirrors")
    if not isinstance(mirrors, list):
        return removed

    for rel in mirrors:
        if not isinstance(rel, str) or not rel.strip():
            continue
        p = project_dir / rel
        if p.is_file():
            p.unlink()
            removed.append(p)
            continue
        if p.is_dir():
            # Mirror paths are typically SKILL.md files; tolerate directory entries too.
            shutil.rmtree(p)
            removed.append(p)
    return removed
