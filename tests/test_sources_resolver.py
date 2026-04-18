import io
import tarfile
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

from skillet.sources.github import (
    GitHubSourceSpec,
    discover_skill_directories,
    fetch_github_skill_directories,
    parse_github_source_spec,
)
from skillet.sources.local import (
    looks_like_local_source_spec,
    resolve_local_skill_directories,
)
from skillet.sources import (
    LocalSourceSpec,
    parse_source_spec,
    resolve_skill_directories,
)


def test_parse_github_variants():
    s = parse_github_source_spec("anthropics/skills")
    assert s.owner == "anthropics"
    assert s.repo == "skills"
    assert s.ref is None
    assert s.skill_subpath is None

    s = parse_github_source_spec("anthropics/skills/skill-creator")
    assert s.skill_subpath == "skill-creator"

    s = parse_github_source_spec("anthropics/skills@my-branch")
    assert s.ref == "my-branch"
    assert s.skill_subpath is None

    s = parse_github_source_spec("anthropics/skills/skill-creator@v1.0.0")
    assert s.ref == "v1.0.0"
    assert s.skill_subpath == "skill-creator"

    s = parse_github_source_spec("org/repo/sub/dir/skill@feature/foo")
    assert s.ref == "feature/foo"
    assert s.skill_subpath == "sub/dir/skill"


def test_parse_github_invalid():
    with pytest.raises(ValueError):
        parse_github_source_spec("nope")
    with pytest.raises(ValueError):
        parse_github_source_spec("owner@repo")


def test_looks_like_local():
    assert looks_like_local_source_spec("./skills/foo") is True
    assert looks_like_local_source_spec("../other") is True
    assert looks_like_local_source_spec("~/Skills/x") is True
    assert looks_like_local_source_spec("/abs/here") is True
    assert looks_like_local_source_spec("anthropics/skills") is False


def test_parse_source_spec_local(tmp_path: Path):
    skill = tmp_path / "my-skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text("---\nname: x\n---\n", encoding="utf-8")
    spec = parse_source_spec(f"./{skill.name}", cwd=tmp_path)
    assert isinstance(spec, LocalSourceSpec)
    assert spec.path == skill.resolve()


def test_resolve_local_single_and_multi(tmp_path: Path):
    root = tmp_path / "repo"
    a = root / "a"
    b = root / "b"
    a.mkdir(parents=True)
    b.mkdir(parents=True)
    (a / "SKILL.md").write_text("---\n---\n", encoding="utf-8")
    (b / "SKILL.md").write_text("---\n---\n", encoding="utf-8")

    dirs = resolve_local_skill_directories(str(a), cwd=tmp_path)
    assert dirs == [a.resolve()]

    dirs = resolve_local_skill_directories(str(root), cwd=tmp_path)
    assert set(dirs) == {a.resolve(), b.resolve()}


def _make_tar_bytes() -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for name, content in (
            ("demo-main/a/SKILL.md", b"---\n---\n"),
            ("demo-main/b/SKILL.md", b"---\n---\n"),
        ):
            ti = tarfile.TarInfo(name=name)
            ti.size = len(content)
            tf.addfile(ti, io.BytesIO(content))
    return buf.getvalue()


def test_fetch_github_mocked(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    archive = _make_tar_bytes()

    def fake_download(*_a, **_k):
        return archive

    monkeypatch.setattr(
        "skillet.sources.github._download_first_available",
        fake_download,
    )

    source = GitHubSourceSpec("o", "r", ref="main", skill_subpath=None)
    dirs, cleanup = fetch_github_skill_directories(source, client=MagicMock())
    try:
        names = sorted(p.name for p in dirs)
        assert names == ["a", "b"]
    finally:
        cleanup()


def test_discover_skips_hidden(tmp_path: Path):
    good = tmp_path / "ok" / "SKILL.md"
    good.parent.mkdir(parents=True)
    good.write_text("x", encoding="utf-8")
    hidden = tmp_path / ".hidden" / "bad" / "SKILL.md"
    hidden.parent.mkdir(parents=True)
    hidden.write_text("x", encoding="utf-8")

    found = discover_skill_directories(tmp_path)
    assert len(found) == 1
    assert found[0].name == "ok"


def test_resolve_skill_directories_local(tmp_path: Path):
    skill = tmp_path / "s"
    skill.mkdir()
    (skill / "SKILL.md").write_text("---\n---\n", encoding="utf-8")
    r = resolve_skill_directories(f"./{skill.name}", cwd=tmp_path)
    try:
        assert len(r.skill_directories) == 1
        assert r.skill_directories[0] == skill.resolve()
    finally:
        r.close()


def test_resolve_github_uses_shared_client():
    archive = _make_tar_bytes()
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.host)
        return httpx.Response(200, content=archive)

    transport = httpx.MockTransport(handler)

    client = httpx.Client(transport=transport)
    try:
        r = resolve_skill_directories(
            "demo/repo@main",
            client=client,
        )
        try:
            assert len(r.skill_directories) == 2
        finally:
            r.close()
    finally:
        client.close()

    assert "codeload.github.com" in calls
