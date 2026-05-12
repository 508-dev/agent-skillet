import shutil
from pathlib import Path

from skillet.installer.lock import existing_mirrors, is_managed, record_skill


def copy_skill(src: Path, dest: Path, *, project_dir: Path | None = None) -> bool:
    """Copy a skill directory to the destination."""
    skill_name = dest.name
    if dest.exists():
        if project_dir is not None and not is_managed(project_dir, skill_name):
            return False
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    return True


def copy_all_skills(
    skills_src: Path,
    skills_dest: Path,
    *,
    project_dir: Path | None = None,
) -> int:
    """Copy all skills from source to destination. Returns count of copied skills."""
    skills_dest.mkdir(parents=True, exist_ok=True)

    count = 0
    for entry in skills_src.iterdir():
        if entry.is_dir() and (entry / "SKILL.md").exists():
            dest = skills_dest / entry.name
            copied = copy_skill(entry, dest, project_dir=project_dir)
            if not copied:
                continue
            if project_dir is not None:
                record_skill(
                    project_dir,
                    entry.name,
                    origin="local:skillet-package",
                    mirrors=existing_mirrors(project_dir, entry.name),
                )
            count += 1

    return count


def remove_skill(skills_dir: Path, skill_name: str) -> bool:
    """Remove a skill by name. Returns True if removed."""
    skill_path = skills_dir / skill_name
    if skill_path.exists():
        shutil.rmtree(skill_path)
        return True
    return False
