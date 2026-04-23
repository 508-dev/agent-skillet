"""Emit mirrored native skill directories (see ``AGENT_NATIVE_SKILL_REL_PATH``)."""

from __future__ import annotations

import shutil
from pathlib import Path

from skillet.config.settings import AGENT_KEYS, AGENT_NATIVE_SKILL_REL_PATH

_LEGACY_TO_REMOVE: tuple[Path, ...] = (
    # Removed in native-only Skillet: migrate away from these paths.
    Path(".cursor/rules/skillet.mdc"),
    Path(".github/copilot-instructions.md"),
)


def _remove_legacy_rule_and_index_files(project_dir: Path) -> None:
    """Delete rule/index files from older Skillet versions if present."""
    for rel in _LEGACY_TO_REMOVE:
        p = project_dir / rel
        if p.is_file():
            p.unlink()
        # Remove empty parent dirs for rules only (e.g. .github if empty)
        if rel.as_posix() == ".github/copilot-instructions.md":
            gh = project_dir / ".github"
            if gh.is_dir() and not any(gh.iterdir()):
                gh.rmdir()


def _native_rel_paths_needed(config: dict) -> set[str]:
    """Relative mirror roots (posix) that should exist for enabled agents."""
    needed: set[str] = set()
    for k in AGENT_KEYS:
        if not config.get(k):
            continue
        rel = AGENT_NATIVE_SKILL_REL_PATH.get(k)
        if rel:
            needed.add(rel)
    return needed


def _prune_disabled_emitters(project_dir: Path, config: dict) -> None:
    """Remove mirrored skill trees when no enabled agent uses that root."""
    needed = _native_rel_paths_needed(config)
    for rel in {p for p in AGENT_NATIVE_SKILL_REL_PATH.values() if p}:
        if rel in needed:
            continue
        tree = project_dir / rel
        if tree.is_dir():
            shutil.rmtree(tree)


def emit_native_skills(skills_dir: Path, dest_root: Path) -> None:
    """Mirror each skill at ``<dest_root>/<name>/SKILL.md`` and prune removed skills.

    ``dest_root`` is a value from ``AGENT_NATIVE_SKILL_REL_PATH`` (e.g. ``.claude/skills``).
    """
    dest_root.mkdir(parents=True, exist_ok=True)

    valid_names: set[str] = set()
    if skills_dir.exists():
        for entry in skills_dir.iterdir():
            if entry.is_dir() and (entry / "SKILL.md").exists():
                valid_names.add(entry.name)

    for child in dest_root.iterdir():
        if child.is_dir() and child.name not in valid_names:
            shutil.rmtree(child)

    for name in sorted(valid_names, key=str.lower):
        src = skills_dir / name / "SKILL.md"
        target_dir = dest_root / name
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target_dir / "SKILL.md")


def emit_claude_code_skills(skills_dir: Path, project_dir: Path) -> None:
    """Mirror each skill under ``.claude/skills/<name>/`` for Claude Code discovery."""
    emit_native_skills(skills_dir, project_dir / ".claude" / "skills")


def write_config_files(skills_dir: Path, project_dir: Path, config: dict) -> dict:
    """Write native skill directory trees for enabled agent targets. Returns paths written."""
    _remove_legacy_rule_and_index_files(project_dir)
    _prune_disabled_emitters(project_dir, config)
    result: dict[str, str] = {}
    seen: set[Path] = set()

    for k in AGENT_KEYS:
        if not config.get(k):
            continue
        rel = AGENT_NATIVE_SKILL_REL_PATH.get(k)
        if not rel:
            continue
        root = project_dir / rel
        if root in seen:
            continue
        seen.add(root)
        emit_native_skills(skills_dir, root)
        key = rel if rel.endswith("/") else f"{rel}/"
        result[key] = str(root)

    return result
