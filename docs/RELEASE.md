# Releasing Agent Skillet

This runbook documents the release process for publishing `agent-skillet` to PyPI.

## When to create the tag

**Tag only after the release commit is on `main`**, not on a feature or PR branch.

- A tag should point at the exact commit that shipped the version bump (the one consumers get from `main`).
- If you tag on a PR branch, the tag may point at a commit that never becomes `main`, or at a squash merge’s parent instead of the merge commit—releases and `release.yml` then won’t match what people actually merged.
- Typical flow: open a PR with the version bump → merge to `main` → `git checkout main && git pull` → create and push the tag on that tip of `main`.

## Preconditions

- You have push access to `main` and can create tags.
- GitHub Actions is enabled for this repository.
- PyPI Trusted Publisher is configured for this repo/workflow (`publish.yml`).
- Local branch is up to date and CI is passing.

## Release flow going forward

```bash
# 1. Bump version in pyproject.toml, merge to main (via PR), then:
git checkout main
git pull origin main

# 2. Create and push a tag (on main, after the version bump is merged)
git tag v0.1.0
git push origin v0.1.0

# 3. On GitHub: Releases -> open auto-created draft release for that tag -> Publish release
#    -> publish.yml triggers automatically
```

## What happens in CI/CD

- Tag push (`v*`) triggers `.github/workflows/release.yml`.
- `release.yml` builds artifacts and creates a **draft** GitHub Release with `dist/*`.
- Publishing that draft release triggers `.github/workflows/publish.yml`.
- `publish.yml` builds again and publishes to PyPI via `pypa/gh-action-pypi-publish`.

## File layout after changes

```text
.github/
  workflows/
    ci.yml
    publish.yml
    release.yml
pyproject.toml      # distribution name is "agent-skillet"
```

## Install docs to update in README (after publish)

```bash
uvx agent-skillet install         # one-off, no install, runs `skillet install`
uv tool install agent-skillet     # global -- puts `skillet` command on PATH
```

## 0.1.0 checklist (dogfooding)

1. Confirm `pyproject.toml` has:
   - `name = "agent-skillet"`
   - `version = "0.1.0"`
2. Merge/rebase latest `main`.
3. Run local checks:
   - `uv sync`
   - `ruff check`
   - `pytest`
4. Open a PR, get review, merge the version bump to `main`.
5. On `main` (`git checkout main && git pull`), create and push tag `v0.1.0`.
6. Wait for `release.yml` to create a draft release.
7. Open GitHub Releases, review draft notes/artifacts, click **Publish release**.
8. Verify `publish.yml` succeeded.
9. Verify package on PyPI:
   - `uvx agent-skillet --version`
10. Smoke test in a clean directory:
    - `uvx agent-skillet init`

## Troubleshooting

- **Release workflow failed: “Tagged commit … is not on origin/main” (or your default branch)**
  - The tag points at a commit that is not in default-branch history. Merge the release to `main`, move or delete the bad tag, and tag again from `main`.

- **Tag/version mismatch in release workflow**
  - `release.yml` enforces `tag == v<project.version>`.
  - Fix either the tag or `pyproject.toml` version so they match.

- **Publish workflow did not run**
  - Ensure you clicked **Publish release** (saving draft is not enough).
  - Ensure release is not marked prerelease; `publish.yml` skips prereleases.

- **PyPI publish auth error**
  - Recheck PyPI Trusted Publisher mapping:
    - Owner/org
    - Repo name
    - Workflow filename `publish.yml`
