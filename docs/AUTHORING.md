# Authoring skills for Skillet

Skills are directories that contain a `SKILL.md` file. The file starts with **YAML frontmatter** (between `---` lines) followed by Markdown instructions for coding agents.

## Required frontmatter

| Field | Meaning |
|-------|---------|
| `name` | Stable id (lowercase, hyphens). Defaults to the parent directory name if omitted. |
| `description` | One-line summary; used in `skillet list` and search. |

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

- **Skills** defaults live in this repository at `skills/` and are copied to `.skillet/skills/` on `skillet install`.
- **Repo-owned** skills live anywhere in your tree (e.g. `./team-skills/checkout-flow/`). Register them with:

  ```bash
  skillet add ./team-skills/checkout-flow
  ```

- **Upstream** skills use GitHub specs compatible with [skills.sh](https://skills.sh/), e.g. `anthropics/skills/skill-creator` or `owner/repo/path/to/skill-dir@branch`.

## Install source selection (`.skillet/config/sources.json`)

`skillet install` and `skillet sync` read `.skillet/config/sources.json` as the single source of truth.

- `kind: "local"` with `"source": "<name>"` resolves to `./skills/<name>/`
- `kind: "local"` with `"path": "<dir>"` resolves directly to that directory
- `kind: "github"` uses the same spec format as `skillet add`

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

On `skillet install`, `skillet sync`, and `skillet add`, Skillet **mirrors** each materialized skill from `.skillet/skills/<name>/` into the enabled agents’ native trees (one `SKILL.md` per skill folder):

| Agent (`agent` key) | Project path |
|--------|----------------|
| Claude Code (`claude`) | `.claude/skills/<name>/SKILL.md` |
| Cursor (`cursor`) | `.cursor/skills/<name>/SKILL.md` |
| OpenCode and other `.agents/skills/` agents (`opencode`, `antigravity`, `cline`, …) | `.agents/skills/<name>/SKILL.md` |
| Qwen Code (`qwen`) | `.qwen/skills/<name>/SKILL.md` |

The `gemini` key in the `agent` list is reserved for future use; in the current version Skillet does **not** write files for it. Use `opencode` (or another `.agents/skills/` agent) if you need that tree. Legacy `ide_support` / `agent_support` in JSON is still read and migrated on save.

## Agent Skills specification

For broader compatibility across tools, see [agentskills.io](https://agentskills.io).
