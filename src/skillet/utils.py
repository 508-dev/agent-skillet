"""Shared utilities for skillet CLI."""

import logging
import os
from pathlib import Path

import click
import httpx

from skillet.config.project import agent_emit_flags_for_project
from skillet.config.settings import load_config
from skillet.installer.emitters import write_config_files
from skillet.installer.lock import load_lock, record_skill
from skillet.skills.parser import parse_skill_file
from skillet.sources import MaterializeSummary, load_sources, upsert_source


# Search API configuration
SEARCH_API_BASE = os.environ.get("SKILLS_API_URL") or "https://skills.sh"

logger = logging.getLogger(__name__)


def search_skills_api(query: str, limit: int = 10) -> list[dict]:
    """Search skills via the skills.sh API."""
    url = f"{SEARCH_API_BASE}/api/search"
    try:
        response = httpx.get(url, params={"q": query, "limit": limit}, timeout=10.0)
    except httpx.TimeoutException as e:
        logger.warning(f"{SEARCH_API_BASE} search timeout: {e} q={query}")
        return []
    except httpx.RequestError as e:
        logger.warning(f"{SEARCH_API_BASE} search request failed: {e} q={query}")
        return []

    if response.status_code != 200:
        body = (response.text or "")[:500]
        logger.warning(
            "skills.sh search non-200: status=%s body=%r q=%r",
            response.status_code,
            body,
            query,
        )
        return []

    try:
        data = response.json()
    except ValueError as e:
        logger.warning("skills.sh search invalid JSON: %s q=%r", e, query)
        return []

    try:
        skills = data.get("skills", [])
        if not isinstance(skills, list):
            skills = []
        results = []
        for skill in skills:
            if not isinstance(skill, dict):
                continue
            results.append(
                {
                    "name": skill.get("name", ""),
                    "slug": skill.get("id", ""),
                    "source": skill.get("source", ""),
                    "installs": skill.get("installs", 0),
                }
            )
        results.sort(key=lambda x: x.get("installs", 0), reverse=True)
        return results
    except Exception:
        logger.exception(
            "skills.sh search unexpected error processing response q=%r", query
        )
        return []


def format_installs(count: int) -> str:
    """Format install count with K/M suffixes."""
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M installs".replace(".0M", "M")
    elif count >= 1_000:
        return f"{count / 1_000:.1f}K installs".replace(".0K", "K")
    elif count > 0:
        return f"{count} install{'s' if count != 1 else ''}"
    return ""


def get_skills_dir(project_dir: Path | None = None) -> Path:
    """Return bundled skills directory from the skillet package."""
    # First, try to find the package's bundled_skills directory
    try:
        import skillet

        pkg_path = Path(skillet.__file__).parent
        bundled = pkg_path / "bundled_skills"
        if bundled.is_dir():
            # Verify it has at least one skill with SKILL.md
            for entry in bundled.iterdir():
                if entry.is_dir() and (entry / "SKILL.md").is_file():
                    return bundled
    except (ImportError, AttributeError):
        pass

    # Fallback: look for skills directory in the skillet source tree (development)
    try:
        import skillet

        pkg_path = Path(skillet.__file__).parent.parent.parent  # Go up to repo root
        dev_checkout = pkg_path / "pyproject.toml"
        dev_git = pkg_path / ".git"
        if not (dev_checkout.is_file() or dev_git.is_dir()):
            raise RuntimeError
        skills_dir = pkg_path / "skills"
        if skills_dir.is_dir():
            for entry in skills_dir.iterdir():
                if entry.is_dir() and (entry / "SKILL.md").is_file():
                    return skills_dir
    except (ImportError, AttributeError, RuntimeError):
        pass

    # Fallback: look for skills directory in the project (for edge cases)
    if project_dir is None:
        project_dir = Path.cwd()
    repo_root = project_dir.resolve()
    bundled = repo_root / "skills"
    if bundled.is_dir():
        for entry in bundled.iterdir():
            if entry.is_dir() and (entry / "SKILL.md").is_file():
                return bundled
    raise RuntimeError("Cannot find bundled skills directory")


def _seed_default_sources(project_dir: Path) -> int:
    """Initialize `.skillet/config/sources.json` with bundled local skills when absent."""
    if load_sources(project_dir):
        return 0
    try:
        bundled = get_skills_dir(project_dir)
    except RuntimeError:
        return 0
    seeded = 0
    for entry in bundled.iterdir():
        if not entry.is_dir() or not (entry / "SKILL.md").is_file():
            continue
        meta = parse_skill_file(entry / "SKILL.md") or {}
        name = str(meta.get("name") or entry.name).strip()
        if not name:
            continue
        upsert_source(
            project_dir,
            name,
            {"kind": "bundled", "source": entry.name},
        )
        seeded += 1
    return seeded


def get_project_skills_dir(project_dir: Path) -> Path:
    return project_dir / ".skillet" / "skills"


def _emit_native_mirrors(project_dir: Path) -> dict[str, str]:
    """Mirror `.skillet/skills` into enabled native agent skill directories."""
    agent_flags = agent_emit_flags_for_project(project_dir)
    project_skills = get_project_skills_dir(project_dir)
    return write_config_files(project_skills, project_dir, agent_flags)


def _github_token() -> str | None:
    t = (os.environ.get("GITHUB_TOKEN") or "").strip()
    if t:
        return t
    return (load_config().get("github_token") or "").strip() or None


def _print_sync_errors(errors: list[str]) -> None:
    for msg in errors:
        click.secho(f"  ! {msg}", fg="red", err=True)


def _sync_footer(errors: list[str]) -> str:
    count = len(errors)
    if count == 0:
        return "✓ Sync complete!"
    noun = "error" if count == 1 else "errors"
    return f"✓ Sync complete! ({count} {noun} during sync)"


def _ensure_project_skills_dir(project_dir: Path) -> Path:
    """Create and return managed project skills directory."""
    project_skills = get_project_skills_dir(project_dir)
    project_skills.mkdir(parents=True, exist_ok=True)
    return project_skills


def _print_mirror_lines(written: dict[str, str], *, suffix: str = "mirrored") -> None:
    """Print mirrored target paths in a consistent CLI format."""
    tail = f" {suffix}" if suffix else ""
    for name, _path in written.items():
        click.echo(f"  ✓ {name}{tail}")


def _print_tracked_sources_count(tracked: int) -> None:
    if tracked == 1:
        click.echo("✓ Tracked 1 skill in .skillet/config/sources.json")
        return
    click.echo(f"✓ Tracked {tracked} skill(s) in .skillet/config/sources.json")


def _origin_from_source_entry(entry: dict) -> str:
    kind = str(entry.get("kind", "")).strip()
    if kind == "github":
        return f"github:{str(entry.get('source', '')).strip()}"
    if kind == "bundled":
        return f"bundled:{str(entry.get('source', '')).strip()}"
    if kind == "local":
        path = str(entry.get("path", "")).strip()
        if path:
            return f"local:{path}"
        source = str(entry.get("source", "")).strip()
        if source:
            return f"local:skills/{source}"
        return "local"
    if kind == "http_zip":
        return f"http_zip:{str(entry.get('url', '')).strip()}"
    return kind or "unknown"


def _record_applied_skills(project_dir: Path, summary: MaterializeSummary) -> None:
    lock = load_lock(project_dir)
    sources = load_sources(project_dir)
    for name in set(summary.added) | set(summary.unchanged):
        source_entry = sources.get(name)
        if not isinstance(source_entry, dict):
            continue
        mirrors: list[str] = []
        skills = lock.get("skills")
        if not isinstance(skills, dict):
            skills = {}
        lock_entry = skills.get(name, {})
        if isinstance(lock_entry, dict) and isinstance(lock_entry.get("mirrors"), list):
            mirrors = [
                m for m in lock_entry["mirrors"] if isinstance(m, str) and m.strip()
            ]
        record_skill(
            project_dir,
            name,
            origin=_origin_from_source_entry(source_entry),
            mirrors=mirrors,
        )


def _materialize_summary_lines(
    summary: MaterializeSummary, *, had_apply_errors: bool
) -> list[str]:
    """Human-readable lines for what changed under `.skillet/skills/`."""
    if had_apply_errors and not (summary.added or summary.removed or summary.unchanged):
        return ["Skills — none successfully materialized (see errors above)."]
    if not (summary.added or summary.removed or summary.unchanged):
        return ["Skills — no changes (sources.json has no skill entries)."]
    parts: list[str] = []
    if summary.added:
        parts.append(f"added: {', '.join(summary.added)}")
    if summary.removed:
        parts.append(f"removed: {', '.join(summary.removed)}")
    if summary.unchanged:
        parts.append(f"unchanged: {', '.join(summary.unchanged)}")
    return [f"Skills — {' · '.join(parts)}"]
