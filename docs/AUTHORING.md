# Authoring skills for Skillet

Skills are directories that contain a `SKILL.md` file. The file starts with **YAML frontmatter** (between `---` lines) followed by Markdown instructions for coding agents.

## Required frontmatter

| Field | Meaning |
|-------|---------|
| `name` | Stable id (lowercase, hyphens). Defaults to the parent directory name if omitted. |
| `description` | One-line summary; used in `skillet list` and find (skills.sh API) / search (local) |

## Example

```markdown
---
name: my-skill
description: When editing payment code, follow these invariants.
---

# My skill

## When to use
- Any change under `src/payments/`

## Steps
1. Read existing tests under `tests/payments/`.
2. …
```

## Where skills live

- **Bundled skills (this repo)** are authored under the repository root `skills/` (one folder per skill with `SKILL.md`). Maintenance edits belong there: **`src/skillet/bundled_skills/` is not the authoring tree**—release CI copies `skills/*` into `src/skillet/bundled_skills/` before building the wheel (see `.github/workflows/build_and_publish.yml`). On `skillet init`, Skillet seeds sources from those bundled definitions and materializes them under `.skillet/skills/<name>/`.
- **Repo-owned** skills live anywhere in your tree (e.g. `./team-skills/checkout-flow/`). Register them with:

  ```bash
  skillet add ./team-skills/checkout-flow
  ```

- **Upstream** skills use GitHub specs compatible with [skills.sh](https://skills.sh/), e.g. `anthropics/skills/skill-creator` or `owner/repo/path/to/skill-dir@branch`.

## Install source selection (`.skillet/config/sources.json`)

`skillet init` and `skillet sync` read `.skillet/config/sources.json` as the single source of truth.

- `kind: "local"` with `"path": "<path-relative-to-project>"` — resolves under your project tree.
- `kind: "local"` with `"source": "<name>"` and no `path` — tries `./skills/<name>/` first, then the skills that ship with the Skillet install (same layout as default `skillet init` seeds). You do not need a special “bundled” type; it is ordinary local resolution.
- `kind: "github"` with `"source": "<owner/repo/subpath[@ref]>"` — same format as `skillet add`.

Example after `skillet init` (default skills from the package / repo `skills/` mirror):

```json
{
  "git-os": {
    "kind": "local",
    "source": "git-os"
  }
}
```

## Where agents load skills (native paths)

On `skillet init`, `skillet sync`, and `skillet add`, Skillet **mirrors** each materialized skill from `.skillet/skills/<name>/` into the enabled agents’ native trees (one `SKILL.md` per skill folder):

| Agent (`agent` key) | Project path |
|--------|----------------|
| Claude Code (`claude`) | `.claude/skills/<name>/SKILL.md` |
| Cursor (`cursor`) | `.cursor/skills/<name>/SKILL.md` |
| OpenCode and other `.agents/skills/` agents (`opencode`, `antigravity`, `cline`, …) | `.agents/skills/<name>/SKILL.md` |
| Qwen Code (`qwen`) | `.qwen/skills/<name>/SKILL.md` |

The `gemini` key in the `agent` list is reserved for future use; in the current version Skillet does **not** write files for it. Use `opencode` (or another `.agents/skills/` agent) if you need that tree. Legacy `ide_support` / `agent_support` in JSON is still read and migrated on save.

## Agent Skills specification

For broader compatibility across tools, see [agentskills.io](https://agentskills.io).
