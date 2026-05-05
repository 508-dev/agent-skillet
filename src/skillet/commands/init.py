"""Init command - initialize Skillet in a directory."""

import click
from pathlib import Path
import shutil

from skillet.utils import (
    get_project_skills_dir,
    _seed_default_sources,
    _ensure_project_skills_dir,
    _github_token,
    apply_all_sources,
    _record_applied_skills,
    _print_sync_errors,
    _materialize_summary_lines,
    ensure_project_agents,
    load_project_config,
    save_project_config,
    _emit_native_mirrors,
    _print_mirror_lines,
    get_project_config_dir,
    PROJECT_CONFIG_VERSION,
)


def _init_command(directory: str, skip_config: bool, skip_bundled: bool) -> None:
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
