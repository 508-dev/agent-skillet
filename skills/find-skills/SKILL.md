---
name: find-skills
description: Helps you discover and install skills from the Agent Skillet ecosystem.
license: MIT
metadata:
  author: skillet
  version: "1.0"
---

# Find Skills

This skill helps you discover and install skills from the Agent Skillet ecosystem.

## When to Use This Skill

Use this skill when the user:

- Asks "how do I do X" where X might be a common task with an existing skill
- Says "find a skill for X" or "is there a skill for X"
- Asks "can you do X" where X is a specialized capability
- Expresses interest in extending agent capabilities
- Wants to search for tools, templates, or workflows
- Mentions they wish they had help with a specific domain (design, testing, deployment, etc.)

## What is Agent Skillet?

Agent Skillet is a tool for managing agent skills in your projects. Skills are modular packages that extend agent capabilities with specialized knowledge, workflows, and tools.

**Key commands:**

- `skillet find [query]` - Search for skills by name or description
- `skillet add <skill>` - Install a skill from local directory or GitHub
- `skillet list` - List all installed skills
- `skillet sync` - Sync all sources from sources.json
- `skillet remove <skill>` - Remove an installed skill

**Browse skills at:** Skills can come from various sources including:
- Bundled skills (included with skillet)
- Local skill directories
- GitHub repositories (e.g., `owner/repo`, `owner/repo/subpath`)

## How to Help Users Find Skills

### Step 1: Understand What They Need

When a user asks for help with something, identify:

1. The domain (e.g., React, testing, design, deployment)
2. The specific task (e.g., writing tests, creating animations, reviewing PRs)
3. Whether this is a common enough task that a skill likely exists

### Step 2: Search for Skills

Run the find command to search for relevant skills:

```bash
skillet find [query]
```

For example:

- User asks "how do I make my React app faster?" → `skillet find react performance`
- User asks "can you help me with PR reviews?" → `skillet find pr review`
- User asks "I need to create a changelog" → `skillet find changelog`

The search looks through skill names and descriptions to find matches.

### Step 3: Evaluate Search Results

When presenting search results to users, consider:

1. **Skill source** — Is it a bundled skill, local skill, or from GitHub?
2. **Description** — Does it clearly address the user's need?
3. **Name** — Is it clearly named for the task at hand?

For bundled skills (included with skillet), users can trust they are well-maintained.

For GitHub skills, you may want to check:
- The source repository's popularity (GitHub stars)
- Recent activity (last commit date)
- Documentation quality

### Step 4: Present Options to the User

When you find relevant skills, present them to the user with:

1. The skill name and what it does
2. The source (bundled, local, or GitHub repo)
3. How to install it

Example response:

```text
I found a skill that might help! The "git-os" skill provides
conventional commits, atomic changes, and GIT-OS workflow guidance.
(Source: bundled with skillet)

To install it:
skillet add git-os
```

### Step 5: Install the Skill

If the user wants to proceed, you can install the skill for them:

```bash
skillet add <skill-name>
```

For GitHub skills, use the full spec:
```bash
skillet add owner/repo/subpath
# Example: skillet add wshobson/agents/python-design-patterns
```

After adding, run sync to materialize the skill:
```bash
skillet sync
```

## Common Skill Categories

When searching, consider these common categories:

| Category | Example Queries |
|----------|-----------------|
| Web Development | react, nextjs, typescript, css, tailwind |
| Testing | testing, jest, playwright, e2e |
| DevOps | deploy, docker, kubernetes, ci-cd |
| Documentation | docs, readme, changelog, api-docs |
| Code Quality | review, lint, refactor, best-practices |
| Design | ui, ux, design-system, accessibility |
| Productivity | workflow, automation, git |

## Tips for Effective Searches

1. **Use specific keywords**: "react testing" is better than just "testing"
2. **Try alternative terms**: If "deploy" doesn't work, try "deployment" or "ci-cd"
3. **Check bundled skills first**: Run `skillet list` to see what's already available
4. **Use GitHub sources**: Many skills come from repositories like `wshobson/agents` or `anthropics/skills`

## When No Skills Are Found

If no relevant skills exist:

1. Acknowledge that no existing skill was found
2. Offer to help with the task directly using your general capabilities
3. Suggest the user could create their own skill

Example:

```text
I searched for skills related to "xyz" but didn't find any matches.
I can still help you with this task directly! Would you like me to proceed?

If this is something you do often, you could create your own skill.
See the documentation at https://github.com/508-dev/agent-skillet/blob/main/docs/AUTHORING.md for guidance.
```
