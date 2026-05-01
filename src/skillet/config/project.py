"""Per-project ``.skillet/config`` and resolved agent flags for emitters.

Each ``agent`` list entry selects whether Skillet mirrors skills into that agent's
native skills directory (project-relative). Exact roots are
``skillet.config.settings.AGENT_NATIVE_SKILL_REL_PATH``; for example:

- ``claude`` → ``.claude/skills/<skill>/SKILL.md``
- ``cursor`` → ``.cursor/skills/<skill>/SKILL.md``
- ``gemini``, ``opencode``, ``antigravity``, ``cline``, ``codex``, ``copilot``, ``kimi`` → shared
  ``.agents/skills/<skill>/SKILL.md``
- ``qwen`` → ``.qwen/skills/<skill>/SKILL.md``

Toggling targets affects only those roots; ``.agents/skills/`` is removed when no
enabled target maps to it.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from skillet.config.settings import (
    AGENT_KEYS,
    load_config,
    normalize_agents,
    read_agents_from_mapping,
)

PROJECT_CONFIG_VERSION = "1"


def get_project_config_dir(project_dir: Path) -> Path:
    return project_dir / ".skillet" / "config"


def project_config_path(project_dir: Path) -> Path:
    return get_project_config_dir(project_dir) / "config.json"


def load_project_config(project_dir: Path) -> dict:
    path = project_config_path(project_dir)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def save_project_config(project_dir: Path, config: dict) -> None:
    """Persist project config; canonical key is ``agent`` (legacy keys are removed)."""
    cfg = dict(config)
    agents = read_agents_from_mapping(cfg)
    if agents:
        cfg["agent"] = agents
    cfg.pop("ide_support", None)
    cfg.pop("agent_support", None)
    get_project_config_dir(project_dir).mkdir(parents=True, exist_ok=True)
    project_config_path(project_dir).write_text(
        json.dumps(cfg, indent=2),
        encoding="utf-8",
    )


def agent_emit_flags_from_global() -> dict[str, bool]:
    """On/off map per agent key from global ``agent`` list (fallback when project unset).

    Keys match ``settings.AGENT_KEYS``. A ``True`` value means that target is enabled;
    native paths are ``settings.AGENT_NATIVE_SKILL_REL_PATH`` (several keys can share
    ``.agents/skills/``).
    """
    config = load_config()
    default_agents = list(AGENT_KEYS)
    keys = list(AGENT_KEYS)
    raw = config.get("agent", default_agents)
    raw_norm = normalize_agents(raw if isinstance(raw, list) else [])
    if not raw_norm:
        raw_norm = default_agents
    flags = {k: k in raw_norm for k in keys}
    if not any(flags.values()):
        return {k: True for k in keys}
    return flags


def agent_emit_flags_for_project(project_dir: Path) -> dict[str, bool]:
    """On/off map: project ``agent`` overrides global when non-empty.

    See `agent_emit_flags_from_global` for key semantics and native path mapping.
    """
    data = load_project_config(project_dir)
    keys = list(AGENT_KEYS)
    proj_agents = read_agents_from_mapping(data)
    if proj_agents:
        flags = {k: k in proj_agents for k in keys}
        if any(flags.values()):
            return flags
    return agent_emit_flags_from_global()


def ensure_project_agents(project_dir: Path) -> None:
    """First-time project setup: prompt (TTY) or copy global defaults for ``agent``."""
    from skillet.config.settings import agent_multiselect_prompt_project
    from skillet.config.wizard import prompt_agent_targets

    valid = frozenset(AGENT_KEYS)
    cfg = load_project_config(project_dir)
    if read_agents_from_mapping(cfg):
        return

    g = load_config().get("agent", list(AGENT_KEYS))
    if not isinstance(g, list) or not g:
        g = list(AGENT_KEYS)

    if sys.stdin.isatty():
        chosen = prompt_agent_targets(
            message=agent_multiselect_prompt_project(),
            hint_previous_keys=[k for k in g if k in valid],
        )
    else:
        chosen = [k for k in g if k in valid] or list(AGENT_KEYS)

    cfg.setdefault("version", PROJECT_CONFIG_VERSION)
    cfg["agent"] = chosen
    save_project_config(project_dir, cfg)
