import json
from pathlib import Path

import pytest


def test_agent_native_paths_cover_all_keys() -> None:
    from skillet.config import settings

    assert set(settings.AGENT_NATIVE_SKILL_REL_PATH) == set(settings.AGENT_KEYS)


def test_format_agent_target_mapping_summary_orders_and_groups_shared_agents_path() -> None:
    from skillet.config.settings import format_agent_target_mapping_summary

    text = format_agent_target_mapping_summary(["gemini", "cursor", "claude"])
    assert ".cursor/skills/" in text
    assert ".claude/skills/" in text
    assert ".agents/skills/" in text
    assert "Gemini CLI" in text
    assert "OpenCode" not in text
    assert text.find(".claude/skills") < text.find(".cursor/skills") < text.find(
        ".agents/skills"
    )
    assert "Native skill directories for enabled agents:" in text

    both = format_agent_target_mapping_summary(["gemini", "opencode"])
    bullet_lines = [ln for ln in both.splitlines() if ln.strip().startswith("•")]
    assert len(bullet_lines) == 1
    assert ".agents/skills/" in bullet_lines[0]
    assert "OpenCode" in both

    shared = format_agent_target_mapping_summary(["opencode", "cline", "codex"])
    assert shared.count(".agents/skills/") == 1
    assert "OpenCode" in shared
    assert "Cline" in shared
    assert "Codex" in shared


def test_save_config_writes_only_lean_keys(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from skillet.config import settings

    fake = tmp_path / "config.json"
    monkeypatch.setattr(settings, "get_config_path", lambda: fake)
    settings.save_config(
        {
            "agent": ["cursor", "gemini"],
            "github_token": "tok",
            "anthropic_api_key": "noise",
        }
    )
    data = json.loads(fake.read_text(encoding="utf-8"))
    assert set(data.keys()) == {"agent", "github_token"}
    assert data["github_token"] == "tok"
    assert data["agent"] == ["cursor", "gemini"]


def test_save_config_migrates_legacy_ide_support_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from skillet.config import settings

    fake = tmp_path / "config.json"
    monkeypatch.setattr(settings, "get_config_path", lambda: fake)
    settings.save_config({"ide_support": ["claude", "opencode"], "github_token": "x"})
    data = json.loads(fake.read_text(encoding="utf-8"))
    assert "ide_support" not in data
    assert data["agent"] == ["claude", "opencode"]
    assert data["github_token"] == "x"


def test_read_agents_from_mapping_prefers_agent_key() -> None:
    from skillet.config.settings import read_agents_from_mapping

    out = read_agents_from_mapping(
        {"agent": ["claude"], "agent_support": ["cursor"], "ide_support": ["qwen"]}
    )
    assert out == ["claude"]


def test_save_config_migrates_legacy_agent_support_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from skillet.config import settings

    fake = tmp_path / "config.json"
    monkeypatch.setattr(settings, "get_config_path", lambda: fake)
    settings.save_config({"agent_support": ["kimi", "qwen"], "github_token": ""})
    data = json.loads(fake.read_text(encoding="utf-8"))
    assert "agent_support" not in data
    assert data["agent"] == ["kimi", "qwen"]
