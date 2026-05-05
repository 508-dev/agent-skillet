import importlib.resources
import os
import shutil
from pathlib import Path

import click
import httpx
import importlib.resources

from skillet import __version__


# Search API configuration
SEARCH_API_BASE = os.environ.get("SKILLS_API_URL") or "https://skills.sh"


def search_skills_api(query: str, limit: int = 10) -> list[dict]:
    """Search skills via the skills.sh API."""
    try:
        url = f"{SEARCH_API_BASE}/api/search"
        response = httpx.get(
            url,
            params={"q": query, "limit": limit},
            timeout=10.0
        )
        if response.status_code == 200:
            data = response.json()
            skills = data.get("skills", [])
            # Transform to our format
            results = []
            for skill in skills:
                results.append({
                    "name": skill.get("name", ""),
                    "slug": skill.get("id", ""),
                    "source": skill.get("source", ""),
                    "installs": skill.get("installs", 0),
                })
            # Sort by installs (descending)
            results.sort(key=lambda x: x.get("installs", 0), reverse=True)
            return results
    except Exception:
        pass
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
from skillet.config.project import (
    PROJECT_CONFIG_VERSION,
    agent_emit_flags_for_project,
    ensure_project_agents,
    get_project_config_dir,
    load_project_config,
    save_project_config,
)
from skillet.config.settings import load_config
from skillet.config.wizard import run_config_wizard
from skillet.installer.copier import remove_skill
from skillet.installer.emitters import write_config_files
from skillet.installer.lock import is_managed, load_lock, record_skill, unrecord_skill
from skillet.skills.parser import parse_skill_file
from skillet.skills.parser import get_skills_from_directory
from skillet.skills.search import search_skills
from skillet.operations.add_sources import add_sources, apply_sources_and_emit
from skillet.sources import (
    MaterializeSummary,
    apply_all_sources,
    load_sources,
    remove_source_entry,
    sources_json_path,
    upsert_source,
)


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
        skills_dir = pkg_path / "skills"
        if skills_dir.is_dir():
            for entry in skills_dir.iterdir():
                if entry.is_dir() and (entry / "SKILL.md").is_file():
                    return skills_dir
    except (ImportError, AttributeError):
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
        # Use absolute path for bundled skills so they can be found at runtime
        upsert_source(project_dir, name, {"kind": "local", "source": entry.name, "path": str(entry.resolve())})
        seeded += 1
    return seeded


def get_project_skills_dir(project_dir: Path) -> Path:
    return project_dir / ".skillet" / "skills"


def _emit_native_mirrors(project_dir: Path) -> dict[str, str]:
    """Mirror ``.skillet/skills`` into enabled native agent skill directories."""
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
    for name in (set(summary.added) | set(summary.unchanged)):
        source_entry = sources.get(name)
        if not isinstance(source_entry, dict):
            continue
        mirrors: list[str] = []
        skills = lock.get("skills")
        if not isinstance(skills, dict):
            skills = {}
        lock_entry = skills.get(name, {})
        if isinstance(lock_entry, dict) and isinstance(lock_entry.get("mirrors"), list):
            mirrors = [m for m in lock_entry["mirrors"] if isinstance(m, str) and m.strip()]
        record_skill(project_dir, name, origin=_origin_from_source_entry(source_entry), mirrors=mirrors)


def _materialize_summary_lines(
    summary: MaterializeSummary, *, had_apply_errors: bool
) -> list[str]:
    """Human-readable lines for what changed under ``.skillet/skills/``."""
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


@click.group(invoke_without_command=True)
@click.version_option(__version__)
@click.pass_context
def main(ctx: click.Context) -> None:
    """Skillet — initialize and sync agent skills into your repo"""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command("init")
@click.argument("directory", default=".")
@click.option(
    "--skip-config",
    is_flag=True,
    help="Skip agent target prompt and native skill directory mirroring",
)
@click.option(
    "--skip-bundled",
    is_flag=True,
    help="Skip installing bundled skills (default: install bundled skills)",
)
def init_cmd(directory: str, skip_config: bool, skip_bundled: bool) -> None:
    """Initialize Skillet in a directory, sync sources, mirror native skill dirs."""
    project_dir = Path(directory).resolve()
    project_skills = get_project_skills_dir(project_dir)

    click.echo(f"\nInitializing Skillet in: {project_dir}")

    get_project_config_dir(project_dir).mkdir(parents=True, exist_ok=True)
    proj_cfg = load_project_config(project_dir)
    proj_cfg.setdefault("version", PROJECT_CONFIG_VERSION)
    save_project_config(project_dir, proj_cfg)

    if not skip_bundled:
        seeded = _seed_default_sources(project_dir)
        if seeded:
            click.echo(f"  ✓ Bootstrapped {seeded} source(s) in .skillet/config/sources.json")

    if project_skills.exists():
        shutil.rmtree(project_skills)
    project_skills = _ensure_project_skills_dir(project_dir)
    token = _github_token()
    install_errors, install_summary = apply_all_sources(
        project_dir, project_skills, github_token=token
    )
    _record_applied_skills(project_dir, install_summary)
    _print_sync_errors(install_errors)
    for line in _materialize_summary_lines(
        install_summary, had_apply_errors=bool(install_errors)
    ):
        click.echo(line)

    if not skip_config:
        ensure_project_agents(project_dir)
        proj_cfg = load_project_config(project_dir)
    save_project_config(project_dir, proj_cfg)

    if not skip_config:
        written = _emit_native_mirrors(project_dir)
        _print_mirror_lines(written)

    click.echo("\n✓ Init complete!")


@main.command("add")
@click.argument("spec")
@click.argument("directory", default=".")
def add(spec: str, directory: str) -> None:
    """Add skills from a local path or a GitHub repository.

    \b
    GitHub spec format:  owner/repo[/subpath][@ref]
    Examples:
      skillet add anthropics/skills/skill-creator
      skillet add anthropics/skills/skill-creator@main
      skillet add myorg/shared-skills

    \b
    Local spec format:   ./path/to/skill-dir
    Example:
      skillet add ./team-skills/checkout-flow
    """
    from skillet.sources import looks_like_local_source_spec

    project_dir = Path(directory).resolve()
    _ensure_project_skills_dir(project_dir)
    token = _github_token()

    tracked, pre_errors = add_sources(
        project_dir,
        [spec],
        skip_existing=False,
        github_token=token,
    )
    _print_sync_errors(pre_errors)

    if tracked == 0:
        if looks_like_local_source_spec(spec) and not pre_errors:
            click.echo(
                "Could not find a local skill directory with SKILL.md. "
                "Pass a path relative to the project or an absolute path."
            )
        elif not pre_errors:
            click.echo("No installable skills found (missing names or empty source).")
        return

    _print_tracked_sources_count(tracked)

    apply_errors, written, add_summary = apply_sources_and_emit(
        project_dir, github_token=token
    )
    _print_sync_errors(apply_errors)
    for line in _materialize_summary_lines(
        add_summary, had_apply_errors=bool(apply_errors)
    ):
        click.echo(line)

    _print_mirror_lines(written)


@main.command("remove")
@click.argument("name")
@click.argument("directory", default=".")
def remove(name: str, directory: str) -> None:
    """Remove an installed skill."""
    project_dir = Path(directory).resolve()
    project_skills = _ensure_project_skills_dir(project_dir)

    if not is_managed(project_dir, name):
        click.echo(f"Skill '{name}' is not managed by Skillet")
        return

    removed_dir = remove_skill(project_skills, name)
    removed_source = remove_source_entry(project_dir, name)
    unrecord_skill(project_dir, name)

    if not removed_dir and not removed_source:
        click.echo(f"Skill '{name}' not found")
        return

    click.echo(f"✓ Removed skill '{name}'")

    if project_skills.exists():
        written = _emit_native_mirrors(project_dir)
        _print_mirror_lines(written)


@main.command("sync")
@click.argument("directory", default=".")
def sync(directory: str) -> None:
    """Read sources from `.skillet/config/sources.json` and sync."""
    project_dir = Path(directory).resolve()
    project_skills = get_project_skills_dir(project_dir)
    has_sources = sources_json_path(project_dir).exists() and load_sources(project_dir)

    if not project_skills.exists() and not has_sources:
        click.echo("No skills installed. Run 'skillet init' first.")
        return

    project_skills = _ensure_project_skills_dir(project_dir)
    token = _github_token()
    source_errors, sync_summary = apply_all_sources(
        project_dir, project_skills, github_token=token
    )
    _record_applied_skills(project_dir, sync_summary)
    _print_sync_errors(source_errors)

    written = _emit_native_mirrors(project_dir)

    click.echo("\nUpdated native skill directories:")
    _print_mirror_lines(written, suffix="")
    for line in _materialize_summary_lines(
        sync_summary, had_apply_errors=bool(source_errors)
    ):
        click.echo(line)
    click.echo(f"\n{_sync_footer(source_errors)}")


@main.command("list")
@click.argument("directory", default=".")
def list_cmd(directory: str) -> None:
    """List all materialized skills."""
    project_dir = Path(directory).resolve()
    project_skills = get_project_skills_dir(project_dir)

    if not project_skills.exists():
        click.echo("No skills installed. Run 'skillet init' first.")
        return

    skills = get_skills_from_directory(project_skills)

    if not skills:
        click.echo("No skills found.")
        return

    click.echo(f"\n{'Name':<25} {'Description':<50}")
    click.echo("-" * 75)
    for skill in skills:
        desc = (
            skill["description"][:47] + "..."
            if len(skill["description"]) > 50
            else skill["description"]
        )
        click.echo(f"{skill['name']:<25} {desc:<50}")
    click.echo(f"\n{len(skills)} skill(s)")


def _search_skills_impl(term: str, directory: str) -> None:
    """Shared implementation for search and find commands."""
    project_dir = Path(directory).resolve()
    project_skills = get_project_skills_dir(project_dir)

    if not project_skills.exists():
        click.echo("No skills installed. Run 'skillet init' first.")
        return

    skills = get_skills_from_directory(project_skills)
    results = search_skills(skills, term)

    if not results:
        click.echo(f"No skills found matching '{term}'")
        return

    click.echo(f"\nSearch results for '{term}':\n")
    for skill in results:
        click.echo(f"  {skill['name']} (score: {skill['score']})")
        if skill["description"]:
            click.echo(f"    {skill['description']}")


@main.command("find")
@click.argument("term")
@click.argument("directory", default=".")
def find_cmd(term: str, directory: str) -> None:
    """Find skills on skills.sh by name or description."""
    if not term or len(term) < 2:
        click.echo("Please provide at least 2 characters to search.")
        return
    
    click.echo(f"Searching skills.sh for '{term}'...")
    skills = search_skills_api(term)
    
    if not skills:
        click.echo(f"No skills found on skills.sh matching '{term}'")
        click.echo("Tip: Try different keywords or check your internet connection.")
        return
    
    click.echo(f"\nFound {len(skills)} skill(s) on skills.sh:\n")
    for skill in skills:
        name = skill.get("name", "")
        slug = skill.get("slug", "")
        source = skill.get("source", "")
        installs = skill.get("installs", 0)
        
        click.echo(f"  {name}")
        if source:
            click.echo(f"    Source: {source}")
        if installs:
            installs_text = format_installs(installs)
            click.echo(f"    {installs_text}")
        if slug:
            click.echo(f"    https://skills.sh/{slug}")
        click.echo()
    
    click.echo("To install a skill: skillet add <owner/repo/path>")
    click.echo("Example: skillet add wshobson/agents/python-design-patterns")


@main.command("search")
@click.argument("term")
@click.argument("directory", default=".")
def search_cmd(term: str, directory: str) -> None:
    """Search local skills by name or description (alias for find)."""
    _search_skills_impl(term, directory)


@main.command("config")
def config_cmd() -> None:
    """Global defaults: agent targets and optional GitHub token for `skillet add`."""
    run_config_wizard()


if __name__ == "__main__":
    main()
