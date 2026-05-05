# Authoring skills for Skillet

Skills are directories that contain a `SKILL.md` file. The file starts with **YAML frontmatter** (between `---` lines) followed by Markdown instructions for coding agents.

## Required frontmatter

| Field | Meaning |
|-------|---------|
| `name` | Stable id (lowercase, hyphens). Defaults to the parent directory name if omitted. |
| `description` | One-line summary; used in `skillet list` and find/search. |

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

- **Bundled skills** live in `src/skillet/bundled_skills/` and are copied to `.skillet/skills/` on `skillet init`. The `path` field in `sources.json` points to the absolute path of the bundled skill.
- **Repo-owned** skills live anywhere in your tree (e.g. `./team-skills/checkout-flow/`). Register them with:

  ```bash
  skillet add ./team-skills/checkout-flow
  ```

- **Upstream** skills use GitHub specs compatible with [skills.sh](https://skills.sh/), e.g. `anthropics/skills/skill-creator` or `owner/repo/path/to/skill-dir@branch`.

## Install source selection (`.skillet/config/sources.json`)

`skillet init` and `skillet sync` read `.skillet/config/sources.json` as the single source of truth.

- `kind: "local"` with `"source": "<name>"` and `"path": "<absolute-dir>"` resolves to that absolute path
- `kind: "local"` with `"source": "<name>"` (no path) resolves to `./skills/<name>/` (legacy behavior)
- `kind: "github"` with `"source": "<owner/repo/subpath[@ref]>"` — same format as `skillet add`

Example: install only local `git-os` (exclude other repo skills):

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
