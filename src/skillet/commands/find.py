"""Find command - search skills.sh API."""

import click
from pathlib import Path

from skillet.utils import format_installs, search_skills_api


def _find_command(term: str, directory: str) -> None:
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
