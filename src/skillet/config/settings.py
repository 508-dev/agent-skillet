"""Shared IDE metadata and global user config (~/.config/skillet/config.json)."""

from __future__ import annotations

import json
from pathlib import Path

IDE_KEYS = ("claude", "cursor", "gemini", "opencode")

# Short product names (hints, reference lines).
IDE_LABELS: dict[str, str] = {
    "claude": "Claude Code",
    "cursor": "Cursor",
    "gemini": "Gemini CLI (reference only; no Skillet file mirror in this version)",
    "opencode": "OpenCode & universal agents (`.agents/skills/`)",
}

# Project-relative roots where Skillet mirrors each skill as ``<name>/SKILL.md``.
# ``gemini`` is a config key for future use; Skillet only mirrors ``.agents/skills/`` for ``opencode``.
IDE_NATIVE_SKILL_REL_PATH: dict[str, str | None] = {
    "claude": ".claude/skills",
    "cursor": ".cursor/skills",
    "gemini": None,
    "opencode": ".agents/skills",
}


def ide_native_skill_rel_path(ide_key: str) -> str | None:
    """Return the mirrored skills directory for ``ide_key``, or ``None`` if there is none."""
    return IDE_NATIVE_SKILL_REL_PATH.get(ide_key)


def ide_emits_native_skill_mirror(ide_key: str) -> bool:
    """Whether Skillet mirrors skills into a native per-agent directory for this target."""
    return ide_native_skill_rel_path(ide_key) is not None


def ide_multiselect_choice_label(ide_key: str) -> str:
    """One-line checkbox label: product name and native path (wizard / project prompts)."""
    if ide_key not in IDE_LABELS:
        return ide_key
    name = IDE_LABELS[ide_key]
    rel = IDE_NATIVE_SKILL_REL_PATH.get(ide_key)
    if rel:
        return f"{name} — {rel}/"
    return f"{name} — (config only; no native skill mirror)"


def format_ide_target_mapping_summary(selected_keys: list[str]) -> str:
    """Human-readable summary of native mirror paths for the given ``ide_support`` list."""
    path_order: list[str] = []
    path_to_names: dict[str, list[str]] = {}
    for key in IDE_KEYS:
        if key not in selected_keys:
            continue
        rel = IDE_NATIVE_SKILL_REL_PATH.get(key)
        if not rel:
            continue
        if rel not in path_to_names:
            path_order.append(rel)
            path_to_names[rel] = []
        path_to_names[rel].append(IDE_LABELS[key])
    lines = [
        f"  • {', '.join(path_to_names[p])}: {p}/" for p in path_order
    ]
    if not lines:
        return ""
    return "Native skill directories for enabled targets:\n" + "\n".join(lines)


def normalize_ide_support(keys: list[str] | None) -> list[str]:
    """Drop unknown keys from stored lists."""
    if not isinstance(keys, list):
        return []
    return [k for k in keys if k in IDE_KEYS]


def ide_checkbox_instruction() -> str:
    return "(Space = select, Enter = confirm; at least one required)"


def ide_multiselect_usage_line() -> str:
    return (
        "Nothing is pre-selected — press Space on each IDE you use, then Enter."
    )


def ide_multiselect_prompt_global() -> str:
    return f"Which IDEs do you use?\n  {ide_multiselect_usage_line()}"


def ide_multiselect_prompt_project() -> str:
    return (
        "Which IDEs should this project target?\n"
        f"  {ide_multiselect_usage_line()}"
    )


def ide_reference_hint_line(keys: list[str]) -> str | None:
    labels = [IDE_LABELS[k] for k in keys if k in IDE_LABELS]
    if not labels:
        return None
    return (
        f"  (For reference: {', '.join(labels)} — use Space to select what applies.)"
    )


def get_config_path() -> Path:
    config_dir = Path.home() / ".config" / "skillet"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.json"


def _lean_config_from_raw(raw: dict | None) -> dict:
    """Only fields Skillet reads; strips legacy keys from older installs."""
    if not isinstance(raw, dict):
        raw = {}
    ide = normalize_ide_support(raw.get("ide_support"))
    if not ide:
        ide = list(IDE_KEYS)
    token = raw.get("github_token")
    gh = token.strip() if isinstance(token, str) else ""
    return {"ide_support": ide, "github_token": gh}


def load_config() -> dict:
    path = get_config_path()
    if path.exists():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            raw = {}
        return _lean_config_from_raw(raw)
    return _lean_config_from_raw({})


def save_config(config: dict) -> None:
    payload = _lean_config_from_raw(config)
    get_config_path().write_text(json.dumps(payload, indent=2), encoding="utf-8")
