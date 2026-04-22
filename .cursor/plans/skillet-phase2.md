# Skillet Phase 2 Plan (Deferred)

## Goal

Add optional, offline recommendation workflows on top of Phase 1:

- `skillet suggest` to infer likely skills from repository signals (no LLM)
- `skillet profile ...` commands to apply/export reusable client profile defaults

Phase 1 behavior (`install/add/remove/sync/list/search/config`) remains unchanged.

## Scope

- Add suggestions and profile features as additive commands.
- Keep everything file-based and local-first.
- No hosted service, no telemetry requirement, no lockfile/versioning changes.

## Functional Requirements

### 1) Offline Suggest

Add CLI command:

- `skillet suggest [directory]`
- `skillet suggest [directory] --profile <id>`
- `skillet suggest [directory] --apply [-y]`

Behavior:

1. Fingerprint project files (read-only), including:
   - `pyproject.toml`, `requirements.txt`, `package.json`
   - Docker files (`Dockerfile`, compose files)
   - `.github/workflows/*`
   - Terraform files/dirs
2. Produce a tag set (example: `python`, `fastapi`, `postgres`, `docker`, `github_actions`, `react`).
3. Rank candidate skill specs via:
   - built-in heuristic rules
   - optional profile signal (if `--profile` supplied)
4. Print ranked suggestions with reasons and score.
5. If `--apply`, call shared add flow to append sources and regenerate outputs.

Constraints:

- no network calls for fingerprinting/scoring itself
- no LLM usage

### 2) Client Profiles

Add profile source locations:

- user: `~/.config/skillet/profiles/*.yaml`
- org: `SKILLET_PROFILES_DIR` (if set; takes precedence)

Profile schema:

```yaml
id: acme-python-api
label: ACME-style Python API
when:
  all: [python, fastapi, postgres]
  any: [docker]
skills:
  - anthropics/skills/skill-creator
notes: Optional text
```

Add CLI group:

- `skillet profile list`
- `skillet profile show <id>`
- `skillet profile apply <id> [directory]`
- `skillet profile export [directory] [--id <id>] [--label <label>] [-o <path>]`

Behavior:

- `list`: print discovered IDs
- `show`: print resolved YAML document
- `apply`: run add flow for all profile `skills` (skip existing)
- `export`: generate starter profile from `.skillet/sources.json`

### 3) Suggest Merge Order

When generating suggestions:

1. explicit `--profile <id>`
2. optional project pointer `.skillet/profile.yaml` (`use_profile: <id>`)
3. built-in heuristics

## Proposed File Additions

- `src/skillet/suggest/__init__.py`
- `src/skillet/suggest/fingerprint.py`
- `src/skillet/suggest/engine.py`
- `src/skillet/profiles/__init__.py`
- `src/skillet/profiles/loader.py`
- `src/skillet/profiles/export_doc.py`

## Proposed File Changes

- `src/skillet/cli.py`
  - add `suggest` command
  - add `profile` subcommands
- `README.md`
  - add suggest/profile usage examples
- `docs/PROFILES.md`
  - profile schema, locations, commands, workflows

## Tests (Phase 2)

Add integration-focused tests:

- fingerprint extraction from representative files
- suggestion ranking includes expected specs for known stacks
- profile loading precedence (`SKILLET_PROFILES_DIR` over user dir)
- `profile list/show`
- `profile export` produces valid YAML with current sources
- `suggest --apply` path updates sources and regenerates outputs

## Non-Goals

- hosted profile registry/marketplace
- lockfile/version pinning
- LLM-based recommendation generation

## Resume Checklist

1. Re-introduce Phase 2 modules under `src/skillet/suggest/` and `src/skillet/profiles/`
2. Wire CLI commands in `src/skillet/cli.py`
3. Add docs (`docs/PROFILES.md`, README updates)
4. Add tests and run:
   - `uv run ruff check src tests`
   - `uv run pytest tests -q`
