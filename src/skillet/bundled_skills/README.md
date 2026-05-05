# Bundled Skills (Build Destination)

This directory is the **build destination** for bundled skills. It gets populated automatically during the CI build process by copying skills from the repository root `skills/` directory.

## Purpose

- **Source of truth**: `skills/` at repository root contains the actual skill files
- **Build destination**: `src/skillet/bundled_skills/` is populated during CI build
- **Runtime location**: When installed from PyPI, the package includes this directory

## For Developers

- **Do NOT manually edit files in this directory** - they will be overwritten during build
- **Do NOT commit skill files to this directory** - they should only exist in `skills/`
- To add/modify bundled skills, edit the files in `skills/` at the repository root
- The CI build script (.github/workflows/publish.yml) handles copying during release

## For AI Agents

When you need to add a new bundled skill:
1. Add the skill directory with SKILL.md to `skills/` at repo root
2. The build process will automatically copy it to this directory
3. Update any relevant documentation (README.md, docs/)

## Build Process

During CI publish workflow, the following step copies skills:
```yaml
- name: Copy bundled skills for packaging
  run: |
    mkdir -p src/skillet/bundled_skills
    cp -r skills/* src/skillet/bundled_skills/
```

This ensures the packaged version includes all bundled skills from the source of truth.
