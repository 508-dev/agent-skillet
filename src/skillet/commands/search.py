"""Search command - search local skills."""

import click
from pathlib import Path

from skillet.skills.search import search_skills
from skillet.skills.parser import get_skills_from_directory
from skillet.utils import get_project_skills_dir


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
        click.echo(f"No skills found matching '{term}'")
        return

    click.echo(f"\nSearch results for '{term}':\n")
    for skill in results:
        click.echo(f"  {skill['name']} (score: {skill['score']})")
        if skill["description"]:
            click.echo(f"    {skill['description']}")
