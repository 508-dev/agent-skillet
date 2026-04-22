from pathlib import Path

from skillet.skills.parser import parse_frontmatter, get_skills_from_directory


def test_parse_frontmatter():
    content = """---
name: test-skill
description: A test skill
metadata:
  author: test
  version: "1.0"
---

# Skill Content
"""
    result = parse_frontmatter(content)
    assert result['name'] == 'test-skill'
    assert result['description'] == 'A test skill'


def test_parse_frontmatter_empty():
    content = "No frontmatter here"
    result = parse_frontmatter(content)
    assert result == {}


def test_get_skills_from_directory():
    from skillet.cli import get_bundled_skills_dir
    bundled = get_bundled_skills_dir()
    skills = get_skills_from_directory(bundled)
    assert len(skills) >= 3
    names = [s['name'] for s in skills]
    assert 'git-os' in names


def test_generate_skills_xml_escapes_markup(tmp_path: Path) -> None:
    from skillet.skills.parser import generate_skills_xml

    skills = [
        {
            "name": "a",
            "description": 'Use <script> & "quotes"',
            "skill_file": str(tmp_path / "a" / "SKILL.md"),
        }
    ]
    xml = generate_skills_xml(skills, tmp_path, rel_location=lambda s: "p<th>ath")
    assert "<script>" not in xml
    assert "&lt;script&gt;" in xml
    assert "&amp;" in xml