"""IDE-facing emitters: native skill directories per agent (Cursor, OpenCode, Claude)."""

from __future__ import annotations

import shutil
from pathlib import Path


def _stale_index_paths(project_dir: Path) -> tuple[Path, ...]:
    return (
        project_dir / "AGENTS.md",
        project_dir / "CLAUDE.md",
        project_dir / "GEMINI.md",
        project_dir / ".cursor" / "rules" / "skillet.mdc",
    )


def _prune_disabled_emitters(project_dir: Path, config: dict) -> None:
    """Remove skill trees and index artifacts for targets that are off."""
    if not config.get("claude"):
        claude_md = project_dir / "CLAUDE.md"
        if claude_md.is_file():
            claude_md.unlink()
        claude_skills = project_dir / ".claude" / "skills"
        if claude_skills.is_dir():
            shutil.rmtree(claude_skills)
    if not config.get("cursor"):
        mdc = project_dir / ".cursor" / "rules" / "skillet.mdc"
        if mdc.is_file():
            mdc.unlink()
        cursor_skills = project_dir / ".cursor" / "skills"
        if cursor_skills.is_dir():
            shutil.rmtree(cursor_skills)
    if not config.get("opencode"):
        agents_skills = project_dir / ".agents" / "skills"
        if agents_skills.is_dir():
            shutil.rmtree(agents_skills)
    if not config.get("gemini"):
        gemini = project_dir / "GEMINI.md"
        if gemini.is_file():
            gemini.unlink()
    if not (
        config.get("claude")
        or config.get("cursor")
        or config.get("gemini")
        or config.get("opencode")
    ):
        agents = project_dir / "AGENTS.md"
        if agents.is_file():
            agents.unlink()


def _remove_stale_index_and_rules(project_dir: Path) -> None:
    """Skillet no longer writes rules/index files; clear any past outputs."""
    for p in _stale_index_paths(project_dir):
        if p.is_file():
            p.unlink()


def _remove_legacy_ide_files(project_dir: Path) -> None:
    """Drop pre–Skillet formats and old rule filenames."""
    legacy = project_dir / ".cursorrules"
    if legacy.is_file():
        legacy.unlink()
    copilot = project_dir / ".github" / "copilot-instructions.md"
    if copilot.is_file():
        copilot.unlink()
    for legacy_rules in (
        project_dir / ".cursor" / "rules" / "openskills.mdc",
        project_dir / ".cursor" / "rules" / "open-skills.mdc",
    ):
        if legacy_rules.is_file():
            legacy_rules.unlink()


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
    _remove_legacy_ide_files(project_dir)
    _remove_stale_index_and_rules(project_dir)
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
