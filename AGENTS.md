# Agent Skillet — map for AI agents

This file is a **navigation index** for automated assistants working in this repository. Read it first to find code, tests, and docs quickly.

## What this repository is

**Agent Skillet** is a Python CLI (`skillet` / `agent-skillet`) that installs, versions, and syncs **agent skills** (directories containing `SKILL.md`) into a project. It tracks sources in `.skillet/config/sources.json`, materializes skills under `.skillet/skills/`, and mirrors them into agent-specific paths (e.g. `.cursor/skills/`, `.claude/skills/`). It supports **local** paths and **GitHub** specs (`owner/repo`, subpaths, `@ref`).

- **Package name:** `agent-skillet` (PyPI)
- **Python:** ≥ 3.12 (`pyproject.toml`)
- **Entry points:** `skillet` and `agent-skillet` → `skillet.cli:main`

## Top-level layout

| Path | Purpose |
|------|---------|
| `src/skillet/` | Main Python package (see below). |
| `skills/` | **Source of truth for bundled skills** — each skill is a folder with `SKILL.md`. Edit here; do not treat `bundled_skills/` as the authoring location. |
| `tests/` | `pytest` suite; mirrors package areas (`test_cli.py`, `test_sources*.py`, `test_emitters.py`, `test_integration.py`, etc.). |
| `docs/` | Human-oriented docs: `AUTHORING.md`, `DEVELOPMENT.md`, `RELEASE.md`. |
| `README.md` | User-facing overview, CLI examples, bundled skill names. |
| `pyproject.toml` | Dependencies, `[project.scripts]`, Ruff, pytest paths, setuptools package discovery. |
| `uv.lock` | Locked deps when using `uv`. |
| `install.sh` | Optional helper to install `uv`. |
| `.github/workflows/` | `ci.yml` (lint + test matrix), `publish.yml` / `release.yml` for releases. |
| `.devcontainer/` | Container-based dev environment. |

Paths starting with `.skillet/` in **this** repo may appear from local `skillet` runs; they are **runtime state** for the tool, not the library source tree.

## Package map (`src/skillet/`)

| Module / path | Role |
|---------------|------|
| `cli.py` | Click CLI: `init`, `add`, `sync`, `list`, `find`, `remove`, configuration, orchestration. **`get_skills_dir()`** resolves bundled skills (package `bundled_skills/`, dev fallbacks to repo `skills/`). |
| `config/project.py` | Project layout, agent emit flags, `.skillet` paths, config load/save. |
| `config/settings.py` | User/tool configuration loading. |
| `config/wizard.py` | Interactive configuration wizard. |
| `installer/copier.py` | Copy/remove skill trees into the project. |
| `installer/emitters.py` | Write agent-facing config files (mirrors). |
| `installer/lock.py` | `skillet.lock` origin recording and managed-skill bookkeeping. |
| `sources/` | **Resolve and fetch skills:** `local.py`, `github.py`, `apply.py`, `store.py`; `load_sources` / `sources_json_path` / apply pipeline. |
| `operations/add_sources.py` | Add sources and run apply + emit. |
| `skills/parser.py` | Parse `SKILL.md` (frontmatter + body). |
| `skills/search.py` | Search / ranking for `skillet find`. |
| `bundled_skills/` | **Packaging destination** for bundled skills (CI copies from `skills/`). Contains `README.md`; **do not hand-edit** for feature work — change root `skills/` instead. |

## Bundled skills (two locations — do not confuse)

1. **`skills/` (repository root)** — where maintainers **author and modify** bundled skills before release.
2. **`src/skillet/bundled_skills/`** — populated for **packaged installs** (see `bundled_skills/README.md` and publish workflow). Prefer editing **`skills/`** in this repo.

At **dev time**, the CLI may resolve bundled skills via `skills/` when the package layout matches the checkout (`cli.py` fallbacks).

## Tests

- **Runner:** `pytest` (config in `pyproject.toml`, `testpaths = ["tests"]`).
- **Suggested commands:** `uv sync` then `uv run ruff check .` and `uv run pytest` (see `README.md` / `docs/DEVELOPMENT.md`).
- **Naming:** `test_<area>.py` maps to the feature area (CLI, sources, emitters, lock, integration).

## Documentation index

| File | Contents |
|------|----------|
| `docs/AUTHORING.md` | Skill format (`SKILL.md` frontmatter), where skills live, adding skills. |
| `docs/DEVELOPMENT.md` | Local setup (`uv` / `pip -e`), running CLI, testing. |
| `docs/RELEASE.md` | Release process. |

## Quick commands (maintainers)

```bash
uv sync --group dev          # install with dev deps
uv run skillet --help       # CLI from source
uv run ruff check .
uv run pytest
```

Editable install: `uv pip install -e .` or `pip install -e ".[dev]"` per `docs/DEVELOPMENT.md`.

## Conventions for agents editing this repo

- Prefer **small, focused changes**; match existing style (Ruff, typing, Click patterns).
- New or changed **bundled skills** → under root **`skills/<name>/SKILL.md`**, plus tests or docs if behavior changes.
- **CLI or sync behavior** → `src/skillet/cli.py` and the relevant `config/` / `installer/` / `sources/` module.
- **New external source types or resolution rules** → `src/skillet/sources/`.
- After code changes, run **lint and tests** before considering the task done.
