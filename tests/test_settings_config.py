import json
from pathlib import Path

import pytest


def test_ide_native_paths_cover_all_keys() -> None:
    from skillet.config import settings

    assert set(settings.IDE_NATIVE_SKILL_REL_PATH) == set(settings.IDE_KEYS)


def test_format_ide_target_mapping_summary_orders_and_groups_shared_agents_path() -> None:
    from skillet.config.settings import format_ide_target_mapping_summary

    text = format_ide_target_mapping_summary(["gemini", "cursor", "claude"])
    assert ".cursor/skills/" in text
    assert ".claude/skills/" in text
    assert ".agents/skills/" not in text
    assert "OpenCode" not in text
    assert text.find(".cursor/skills") > text.find(".claude/skills")

    both = format_ide_target_mapping_summary(["gemini", "opencode"])
    bullet_lines = [ln for ln in both.splitlines() if ln.strip().startswith("•")]
    assert len(bullet_lines) == 1
    assert ".agents/skills/" in bullet_lines[0]
    assert "OpenCode" in both


def test_save_config_writes_only_lean_keys(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from skillet.config import settings

    fake = tmp_path / "config.json"
    monkeypatch.setattr(settings, "get_config_path", lambda: fake)
    settings.save_config(
        {
            "ide_support": ["cursor", "gemini"],
            "github_token": "tok",
            "anthropic_api_key": "noise",
        }
    )
    data = json.loads(fake.read_text(encoding="utf-8"))
    assert set(data.keys()) == {"ide_support", "github_token"}
    assert data["github_token"] == "tok"
    assert data["ide_support"] == ["cursor", "gemini"]
