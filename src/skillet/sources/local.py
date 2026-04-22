"""Resolve skills from a local directory (./path or absolute)."""

from __future__ import annotations

from pathlib import Path

from skillet.sources.github import discover_skill_directories


def looks_like_local_source_spec(spec: str) -> bool:
    """True if the spec should be treated as a filesystem path, not GitHub."""
    s = spec.strip()
    if not s:
        return False
    if s.startswith(("./", "../", "~/", "~\\")):
        return True
    return Path(s).is_absolute()


def resolve_local_skill_path(spec: str, *, cwd: Path) -> Path:
    """Return an absolute, resolved path to the local skill or repo directory."""
    raw = spec.strip()
    p = Path(raw)
    if raw.startswith("~/") or raw.startswith("~\\"):
        p = Path(raw).expanduser()
    elif not p.is_absolute():
        p = (cwd / p).resolve()
    else:
        p = p.resolve()
    if not p.exists():
        msg = f"Local path does not exist: {p}"
        raise FileNotFoundError(msg)
    return p


def resolve_local_skill_directories(spec: str, *, cwd: Path) -> list[Path]:
    """
    If the path is a skill directory (contains SKILL.md), return [path].

    Otherwise treat it as a repo root and return every subdirectory with SKILL.md.
    """
    path = resolve_local_skill_path(spec, cwd=cwd)
    if path.is_file():
        msg = f"Expected a directory, got file: {path}"
        raise ValueError(msg)
    if (path / "SKILL.md").is_file():
        return [path]
    dirs = discover_skill_directories(path)
    if not dirs:
        msg = f"No SKILL.md found under {path}"
        raise ValueError(msg)
    return dirs
