"""Skillet CLI - thin entry points to command implementations."""

import sys

import click
from pathlib import Path

from skillet import __version__
from skillet.config.wizard import run_config_wizard
from skillet.installer.copier import remove_skill
from skillet.installer.lock import is_managed, unrecord_skill
from skillet.operations.add_sources import add_sources, apply_sources_and_emit
from skillet.skills.parser import get_skills_from_directory
from skillet.sources import (
    apply_all_sources,
    load_sources,
    remove_source_entry,
    sources_json_path,
)
from skillet.utils import (
    _emit_native_mirrors,
    _ensure_project_skills_dir,
    _github_token,
    _materialize_summary_lines,
    _print_mirror_lines,
    _print_sync_errors,
    _print_tracked_sources_count,
    _record_applied_skills,
    _sync_footer,
    get_project_skills_dir,
)
from skillet.commands import _find_command, _search_command, _init_command

# Block-letter banner (UTF-8); shown before each subcommand unless --help / -h.
_SKILLET_BANNER = """\

███████╗██╗  ██╗██╗██╗     ██╗     ███████╗████████╗
██╔════╝██║ ██╔╝██║██║     ██║     ██╔════╝   ██╔══╝
███████╗█████╔╝ ██║██║     ██║     ███████╝   ██║
╚════██║██╔═██╗ ██║██║     ██║     ██╔════╝   ██║
███████║██║  ██╗██║███████╗███████╗███████╝   ██║
╚══════╝╚═╝  ╚═╝╚═╝╚══════╝╚══════╝╚══════╝   ╚═╝
"""


def _argv_requests_help() -> bool:
    return any(a in ("-h", "--help") for a in sys.argv[1:])


@click.group(invoke_without_command=True)
@click.version_option(__version__)
@click.pass_context
def main(ctx: click.Context) -> None:
    """Skillet — initialize and sync agent skills into your repo"""
    if ctx.invoked_subcommand is not None and not _argv_requests_help():
        click.echo(_SKILLET_BANNER)
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
    _init_command(directory, skip_config, skip_bundled)


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


@main.command("find")
@click.argument("term")
def find_cmd(term: str) -> None:
    """Find skills on skills.sh by name or description."""
    _find_command(term)


@main.command("search")
@click.argument("term")
@click.argument("directory", default=".")
def search_cmd(term: str, directory: str) -> None:
    """Search local skills by name or description."""
    _search_command(term, directory)


@main.command("config")
def config_cmd() -> None:
    """Global defaults: agent targets and optional GitHub token for `skillet add`."""
    run_config_wizard()


if __name__ == "__main__":
    main()
