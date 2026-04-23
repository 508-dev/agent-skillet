import json
from pathlib import Path

from skillet.config.project import agent_emit_flags_for_project, save_project_config


def test_agent_emit_flags_read_legacy_project_agent_support(tmp_path: Path) -> None:
    cfg_dir = tmp_path / ".skillet" / "config"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "config.json").write_text(
        json.dumps({"version": "1", "agent_support": ["opencode"]}),
        encoding="utf-8",
    )
    flags = agent_emit_flags_for_project(tmp_path)
    assert flags["opencode"] is True
    assert flags["claude"] is False


def test_agent_emit_flags_read_legacy_project_ide_support(tmp_path: Path) -> None:
    cfg_dir = tmp_path / ".skillet" / "config"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "config.json").write_text(
        json.dumps({"version": "1", "ide_support": ["qwen", "claude"]}),
        encoding="utf-8",
    )
    flags = agent_emit_flags_for_project(tmp_path)
    assert flags["qwen"] is True
    assert flags["claude"] is True
    assert flags["cursor"] is False


def test_save_project_config_migrates_ide_support_key(tmp_path: Path) -> None:
    from skillet.config.project import PROJECT_CONFIG_VERSION

    save_project_config(
        tmp_path,
        {"version": PROJECT_CONFIG_VERSION, "ide_support": ["cursor"]},
    )
    raw = json.loads(
        (tmp_path / ".skillet" / "config" / "config.json").read_text(encoding="utf-8")
    )
    assert "ide_support" not in raw
    assert raw["agent"] == ["cursor"]
    assert "agent_support" not in raw
    assert agent_emit_flags_for_project(tmp_path)["cursor"] is True
