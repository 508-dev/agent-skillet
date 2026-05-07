# Agent Skillet

[![CI](https://github.com/508-dev/agent-skillet/actions/workflows/ci.yml/badge.svg)](https://github.com/508-dev/agent-skillet/actions/workflows/ci.yml)

Prepare and serve agent skills!

Agent Skillet helps teams install, version, and sync agent skills inside a repository.

## Install

### From PyPI (recommended)

```bash
uvx agent-skillet init
uv tool install agent-skillet
```

### From source (development)

```bash
uv pip install -e .
```

If you do not already have `uv`, run:

```bash
zsh install.sh
```

## Quick Start

1. Initialize Skillet in your project

   ```bash
   skillet init
   ```

   This command prompts which agentic coding tool you're using, then
   - Seeds current project managed by skillet with every bundled skill in `skills` folder
   - Materializes them under `.skillet/skills/<skill_name>/`, and mirrors into configured agent folders

2. Add new skills from Github (`owner/repo` or `owner/repo/path[@ref]`):

   ```bash
   skillet add anthropics/skills/frontend-design@main
   ```

## Configuration

1. To configure which agentic coding tool(s) skills show up for (Cursor, Claude Code, and other agents each have their own mirror paths):

   ```bash
   skillet config    # update your agentic coding tool
   skillet sync      # sync skills to your new destination
   ```

## Browse skills

1. Browse skills publicly with `skillet find <query>` or local ones with `skillet search <query>`.

## How It Works

- Tracks installed skill sources in `.skillet/config/sources.json`.
- Materializes installed skills into `.skillet/skills/<name>/SKILL.md`.
- Mirrors enabled skills into agent-native directories (for example `.cursor/skills/` and `.claude/skills/`).
- Supports local sources and GitHub specs (`owner/repo`, `owner/repo/subpath`, `owner/repo/subpath@ref`).
- **GitHub installs** download GitHub’s **full repository archive tarball** for the resolved ref, then copy to the skill folder from your path segment

### Example `sources.json`

Each entry maps a skill name to its source. The `kind` field is either `"local"` or `"github"`.

```json
{
  "git-os": {
    "kind": "local",
    "source": "git-os"
  },
  "python-design-patterns": {
    "kind": "github",
    "source": "wshobson/agents/python-design-patterns@main"
  },
  "skill-creator": {
    "kind": "github",
    "source": "anthropics/skills/skill-creator"
  }
}
```

`skillet add` writes these entries for you — you rarely need to edit the file directly.

## Common Commands Examples

```bash
# Add a local skill directory (must contain SKILL.md)
skillet add ./team-skills/checkout-flow

# Add all skills from a GitHub repo (owner/repo)
skillet add wshobson/agents

# Add a single skill from a GitHub repo (owner/repo/subpath)
skillet add anthropics/skills/skill-creator

# Pin to a specific branch or tag (owner/repo/subpath@ref)
skillet add wshobson/agents/python-design-patterns@main

# Re-sync all sources after editing .skillet/config/sources.json
skillet sync

# Find skills on skills.sh
skillet find <query>

# Search local skills
skillet search <query>

# List installed skills
skillet list

# Remove a skill
skillet remove skill-creator
```

> **Tip:** `skillet.lock` records origins with a `github:` prefix
> (e.g. `github:anthropics/skills/skill-creator`). `skillet add` accepts
> both forms, so you can copy-paste a lock origin directly as a spec.

## Bundled Skills

- `find-skills`: Discover and install skills from the Agent Skillet ecosystem
- `git-os`: Conventional commits, atomic changes, and GIT-OS workflow
- `sprint`: Ticket-to-PR automation with branch and description templates
- `deploy-checklist`: Pre/post deployment verification checklist

## Documentation

- [Authoring skills](docs/AUTHORING.md)
- [Development guide](docs/DEVELOPMENT.md)
- [Releasing](docs/RELEASE.md)

## Contributing

Contributions are welcome and encouraged.

- Open an issue first for bug reports, feature requests, or design discussion.
- Keep pull requests focused and small; include clear context in the description.
- Add or update tests when behavior changes.
- Run local checks before opening a PR:

```bash
uv sync
ruff check
pytest
```

- Be respectful and collaborative in reviews so we can keep the project healthy and active!

## License

MIT
