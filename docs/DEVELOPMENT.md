# Development Guide

This guide explains how to set up a development environment for Agent Skillet and test changes locally before publishing.

## Prerequisites

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Setting Up Development Environment

### Using uv (recommended)

```bash
# Clone the repository
git clone https://github.com/508-dev/agent-skillet.git
cd agent-skillet

# Install dependencies (including dev dependencies)
uv sync
```

This creates a virtual environment at `.venv/` and installs all dependencies.

### Using pip

```bash
# Clone the repository
git clone https://github.com/508-dev/agent-skillet.git
cd agent-skillet

# Install in editable mode
pip install -e ".[dev]"
```

## Running the Local Version

### Option 1: Using `uv run` (easiest)

Run skillet directly from the source without installing:

```bash
# Run skillet commands using uv run
uv run skillet --help
uv run skillet init
uv run skillet find <query>  # Primary search command
uv run skillet search <query>  # Alias for find
```

The `uv run` command automatically uses the local source code in `src/`.

### Option 2: Editable install

Install the package in editable mode so changes to the source code take effect immediately:

```bash
# Install in editable mode
uv pip install -e .

# Now you can run skillet directly
skillet --help
skillet init
```

With editable install, you don't need `uv run` prefix.

### Option 3: Test in a separate project

To test the local version in a different project:

```bash
# In your test project directory
cd /path/to/test-project

# Run using the development version
uv run --project /path/to/agent-skillet skillet init
```

This runs the skillet command from your development copy.

## Testing Changes

### Run the test suite

```bash
# Using uv
uv run pytest

# With coverage
uv run pytest --cov=skillet --cov-report=term-missing
```

### Manual testing workflow

1. Make changes to the code
2. Test using `uv run skillet <command>` or editable install
3. Verify the behavior in a test project:

```bash
# Create a test project
mkdir -p /tmp/test-project && cd /tmp/test-project

# Test init with local version
uv run --project /path/to/agent-skillet skillet init

# Verify skills are installed
cat .skillet/config/sources.json
ls -la .skillet/skills/

# Test find command
uv run --project /path/to/agent-skillet skillet find git
# Alias also works: uv run --project /path/to/agent-skillet skillet search git
```

## Before Publishing

1. Run the full test suite: `uv run pytest`
2. Check code style: `uv run ruff check src/`
3. Update version in `pyproject.toml` (see [RELEASE.md](RELEASE.md) for details)
4. Test the package build: `uv build`
5. Follow the release process in [RELEASE.md](RELEASE.md)

## Project Structure

```
agent-skillet/
├── src/skillet/          # Main package source code
│   ├── cli.py            # CLI commands
│   ├── bundled_skills/   # Bundled skills shipped with the package
│   └── ...
├── skills/               # Skill files (also at repo root for development)
├── docs/                 # Documentation
├── tests/                # Test suite
├── pyproject.toml        # Project configuration
└── README.md             # Project readme
```

## Tips

- Use `uv run skillet` during development to ensure you're running the local version
- For quick testing, use `uv run --project /path/to/agent-skillet skillet` from any directory
- The `skills/` directory at the repo root mirrors `src/skillet/bundled_skills/` for development convenience
- After making changes to bundled skills, copy them to `src/skillet/bundled_skills/` for testing
