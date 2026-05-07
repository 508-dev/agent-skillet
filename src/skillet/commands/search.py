"""Search command - search local skills."""

import shutil
import textwrap
from pathlib import Path

import click

from skillet.skills.search import search_skills
from skillet.skills.parser import get_skills_from_directory
from skillet.utils import get_project_skills_dir


def _text_width() -> int:
    try:
        return max(48, min(96, shutil.get_terminal_size().columns - 4))
    except OSError:
        return 76


def _search_command(term: str, directory: str) -> None:
    """Search local skills by name or description."""
    project_dir = Path(directory).resolve()
    project_skills = get_project_skills_dir(project_dir)

    if not project_skills.exists():
        click.echo("No skills installed. Run 'skillet init' first.")
        return

    skills = get_skills_from_directory(project_skills)
    results = search_skills(skills, term)

    if not results:
        rel = project_skills.relative_to(project_dir).as_posix()
        click.echo(
            f"No skills installed in this project match '{term}' "
            f"(search is limited to {rel}/)."
        )
        return

    n = len(results)
    noun = "skill" if n == 1 else "skills"
    click.echo()
    click.echo(
        click.style(f"Search results for {term!r}", bold=True)
        + f" — {n} {noun} in "
        + f"{project_skills.relative_to(project_dir).as_posix()}/"
    )
    click.echo()

    width = _text_width()
    sep = "─" * min(width, 72)

    for i, skill in enumerate(results):
        if i > 0:
            click.echo()
            click.echo(sep)
            click.echo()

        name = skill["name"]
        score = skill["score"]
        click.echo(click.style(f"{i + 1}. {name}", bold=True))
        click.echo(f"   Match score: {score}")
        desc = (skill.get("description") or "").strip()
        if desc:
            click.echo()
            wrapped = textwrap.fill(
                desc,
                width=width,
                initial_indent="   ",
                subsequent_indent="   ",
            )
            click.echo(wrapped)
