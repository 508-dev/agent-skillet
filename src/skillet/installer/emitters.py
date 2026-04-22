"""Emit mirrored native skill directories (``.claude/skills``, ``.cursor/skills``, ``.agents/skills``)."""

from __future__ import annotations

import shutil
from pathlib import Path

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


def _prune_disabled_emitters(project_dir: Path, config: dict) -> None:
    """Remove mirrored skill trees for IDE targets that are off."""
    if not config.get("claude"):
        claude_skills = project_dir / ".claude" / "skills"
        if claude_skills.is_dir():
            shutil.rmtree(claude_skills)
    if not config.get("cursor"):
        cursor_skills = project_dir / ".cursor" / "skills"
        if cursor_skills.is_dir():
            shutil.rmtree(cursor_skills)
    if not config.get("opencode"):
        agents_skills = project_dir / ".agents" / "skills"
        if agents_skills.is_dir():
            shutil.rmtree(agents_skills)


def emit_native_skills(skills_dir: Path, dest_root: Path) -> None:
    """Mirror each skill at ``<dest_root>/<name>/SKILL.md`` and prune removed skills.

    ``dest_root`` is one of: ``.claude/skills``, ``.cursor/skills``, ``.agents/skills``.
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
    """Write native skill directory trees for enabled IDE targets. Returns paths written."""
    _remove_legacy_rule_and_index_files(project_dir)
    _prune_disabled_emitters(project_dir, config)
    result: dict[str, str] = {}

    if config.get("claude"):
        root = project_dir / ".claude" / "skills"
        emit_native_skills(skills_dir, root)
        result[".claude/skills/"] = str(root)

    if config.get("cursor"):
        root = project_dir / ".cursor" / "skills"
        emit_native_skills(skills_dir, root)
        result[".cursor/skills/"] = str(root)

    if config.get("opencode"):
        root = project_dir / ".agents" / "skills"
        emit_native_skills(skills_dir, root)
        result[".agents/skills/"] = str(root)

    return result
