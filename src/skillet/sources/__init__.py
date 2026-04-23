"""Source spec resolution: GitHub (skills.sh-style) and local paths."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import httpx

from skillet.sources.github import (
    GitHubSourceSpec,
    fetch_github_skill_directories,
    parse_github_source_spec,
    serialize_github_source_spec,
)
from skillet.sources.local import (
    looks_like_local_source_spec,
    resolve_local_skill_directories,
    resolve_local_skill_path,
)
from skillet.sources.apply import MaterializeSummary, apply_all_sources
from skillet.sources.store import (
    load_sources,
    remove_source_entry,
    sources_json_path,
    upsert_source,
)

__all__ = [
    "GitHubSourceSpec",
    "LocalSourceSpec",
    "ResolvedSkills",
    "fetch_github_skill_directories",
    "looks_like_local_source_spec",
    "parse_github_source_spec",
    "parse_source_spec",
    "resolve_github_skill_directories",
    "resolve_local_skill_directories",
    "resolve_local_skill_path",
    "resolve_skill_directories",
    "resolving",
    "serialize_github_source_spec",
    "MaterializeSummary",
    "apply_all_sources",
    "load_sources",
    "remove_source_entry",
    "sources_json_path",
    "upsert_source",
]


@dataclass(frozen=True)
class LocalSourceSpec:
    """Normalized local source; path is absolute."""

    path: Path


def parse_source_spec(spec: str, *, cwd: Path) -> GitHubSourceSpec | LocalSourceSpec:
    """Parse a user source string into either a GitHub or local spec."""
    if looks_like_local_source_spec(spec):
        return LocalSourceSpec(path=resolve_local_skill_path(spec, cwd=cwd))
    return parse_github_source_spec(spec)


@dataclass
class ResolvedSkills:
    """Absolute paths to skill directories (each contains SKILL.md)."""

    skill_directories: list[Path]
    _cleanup: Callable[[], None] | None = None

    def close(self) -> None:
        if self._cleanup is not None:
            self._cleanup()
            self._cleanup = None


def resolve_github_skill_directories(
    spec: str,
    *,
    cwd: Path,  # noqa: ARG001 — API symmetry with resolve_skill_directories
    token: str | None = None,
    client: httpx.Client | None = None,
) -> ResolvedSkills:
    gh = parse_github_source_spec(spec)
    dirs, cleanup = fetch_github_skill_directories(gh, token=token, client=client)
    return ResolvedSkills(skill_directories=dirs, _cleanup=cleanup)


def resolve_skill_directories(
    spec: str,
    *,
    cwd: Path | None = None,
    token: str | None = None,
    client: httpx.Client | None = None,
) -> ResolvedSkills:
    """
    Resolve any supported source spec to skill directories.

    For GitHub sources, call ``.close()`` on the result when finished copying files,
    or use :func:`resolving` context manager.
    """
    base = cwd or Path.cwd()
    if looks_like_local_source_spec(spec):
        dirs = resolve_local_skill_directories(spec, cwd=base)
        return ResolvedSkills(skill_directories=dirs, _cleanup=None)
    return resolve_github_skill_directories(
        spec, cwd=base, token=token, client=client
    )


@contextmanager
def resolving(
    spec: str,
    *,
    cwd: Path | None = None,
    token: str | None = None,
    client: httpx.Client | None = None,
) -> Iterator[ResolvedSkills]:
    """Context manager that cleans up temporary GitHub extraction on exit."""
    r = resolve_skill_directories(spec, cwd=cwd, token=token, client=client)
    try:
        yield r
    finally:
        r.close()
