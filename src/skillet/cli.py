import os
import shutil
from pathlib import Path

import click

from skillet import __version__
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
from skillet.skills.parser import parse_skill_file
from skillet.skills.parser import get_skills_from_directory
from skillet.skills.search import search_skills
from skillet.operations.add_specs import add_specs, apply_sources_and_emit
from skillet.sources import (
    MaterializeSummary,
    apply_all_sources,
    load_sources,
    remove_source_entry,
    sources_json_path,
    upsert_source,
)


def get_skills_dir(project_dir: Path | None = None) -> Path:
    """Return local repository ``skills/`` directory for this project."""
    repo_root = (project_dir or Path.cwd()).resolve()
    bundled = repo_root / "skills"
    if bundled.is_dir():
        for entry in bundled.iterdir():
            if entry.is_dir() and (entry / "SKILL.md").is_file():
                return bundled
    raise RuntimeError("Cannot find bundled skills at repository root: skills/")


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
        upsert_source(project_dir, name, {"kind": "local", "source": entry.name})
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
    """Skillet — install and sync agent skills into your repo"""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command("install")
@click.argument("directory", default=".")
@click.option(
    "--skip-config",
    is_flag=True,
    help="Skip agent target prompt and native skill directory mirroring",
)
def install(directory: str, skip_config: bool) -> None:
    """Set up ``.skillet/skills/``, sync sources, prompt for agent targets once, mirror native skill dirs."""
    project_dir = Path(directory).resolve()
    project_skills = get_project_skills_dir(project_dir)

    click.echo(f"\nInstalling Skillet to: {project_dir}")

    get_project_config_dir(project_dir).mkdir(parents=True, exist_ok=True)
    proj_cfg = load_project_config(project_dir)
    proj_cfg.setdefault("version", PROJECT_CONFIG_VERSION)
    save_project_config(project_dir, proj_cfg)

    seeded = _seed_default_sources(project_dir)
    if seeded:
        click.echo(f"  ✓ Bootstrapped {seeded} source(s) in .skillet/config/sources.json")

    if project_skills.exists():
        shutil.rmtree(project_skills)
    project_skills.mkdir(parents=True, exist_ok=True)
    token = _github_token()
    install_errors, install_summary = apply_all_sources(
        project_dir, project_skills, github_token=token
    )
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
        for name, _path in written.items():
            click.echo(f"  ✓ {name} mirrored")

    click.echo("\n✓ Installation complete!")


@main.command("add")
@click.argument("spec")
@click.argument("directory", default=".")
def add(spec: str, directory: str) -> None:
    """Add skills from a local directory or GitHub (``owner/repo[/path][@ref]``)."""
    from skillet.sources import looks_like_local_source_spec

    project_dir = Path(directory).resolve()
    project_skills = get_project_skills_dir(project_dir)
    project_skills.mkdir(parents=True, exist_ok=True)
    token = _github_token()

    tracked, pre_errors = add_specs(
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

    if tracked == 1:
        click.echo("✓ Tracked 1 skill in .skillet/config/sources.json")
    else:
        click.echo(f"✓ Tracked {tracked} skill(s) in .skillet/config/sources.json")

    apply_errors, written, add_summary = apply_sources_and_emit(
        project_dir, github_token=token
    )
    _print_sync_errors(apply_errors)
    for line in _materialize_summary_lines(
        add_summary, had_apply_errors=bool(apply_errors)
    ):
        click.echo(line)

    for fname, _ in written.items():
        click.echo(f"  ✓ {fname} mirrored")


@main.command("remove")
@click.argument("name")
@click.argument("directory", default=".")
def remove(name: str, directory: str) -> None:
    """Remove an installed skill from ``.skillet/skills/`` and ``.skillet/config/sources.json``."""
    project_dir = Path(directory).resolve()
    project_skills = get_project_skills_dir(project_dir)

    if not project_skills.exists():
        project_skills.mkdir(parents=True, exist_ok=True)

    removed_dir = remove_skill(project_skills, name)
    removed_source = remove_source_entry(project_dir, name)

    if not removed_dir and not removed_source:
        click.echo(f"Skill '{name}' not found")
        return

    click.echo(f"✓ Removed skill '{name}'")

    if project_skills.exists():
        written = _emit_native_mirrors(project_dir)
        for fname, _ in written.items():
            click.echo(f"  ✓ {fname} mirrored")


@main.command("sync")
@click.argument("directory", default=".")
def sync(directory: str) -> None:
    """Re-fetch sources from ``.skillet/config/sources.json`` and refresh native skill directory mirrors."""
    project_dir = Path(directory).resolve()
    project_skills = get_project_skills_dir(project_dir)
    has_sources = sources_json_path(project_dir).exists() and load_sources(project_dir)

    if not project_skills.exists() and not has_sources:
        click.echo("No skills installed. Run 'skillet install' first.")
        return

    project_skills.mkdir(parents=True, exist_ok=True)
    token = _github_token()
    source_errors, sync_summary = apply_all_sources(
        project_dir, project_skills, github_token=token
    )
    _print_sync_errors(source_errors)

    written = _emit_native_mirrors(project_dir)

    click.echo("\nUpdated native skill directories:")
    for name, _path in written.items():
        click.echo(f"  ✓ {name}")
    for line in _materialize_summary_lines(
        sync_summary, had_apply_errors=bool(source_errors)
    ):
        click.echo(line)
    click.echo(f"\n{_sync_footer(source_errors)}")


@main.command("list")
@click.argument("directory", default=".")
def list_cmd(directory: str) -> None:
    """List installed skills under ``.skillet/skills/``."""
    project_dir = Path(directory).resolve()
    project_skills = get_project_skills_dir(project_dir)

    if not project_skills.exists():
        click.echo("No skills installed. Run 'skillet install' first.")
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


@main.command("search")
@click.argument("term")
@click.argument("directory", default=".")
def search_cmd(term: str, directory: str) -> None:
    """Search installed skills by name or description."""
    project_dir = Path(directory).resolve()
    project_skills = get_project_skills_dir(project_dir)

    if not project_skills.exists():
        click.echo("No skills installed. Run 'skillet install' first.")
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


@main.command("config")
def config_cmd() -> None:
    """Global defaults: agent targets and optional GitHub token for `skillet add`."""
    run_config_wizard()


if __name__ == "__main__":
    main()
