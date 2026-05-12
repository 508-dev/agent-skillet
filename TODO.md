# TODO

Track deferred enhancements and product follow-ups here.

## Backlog

- [ ] Track remote identity for GitHub sources in `.skillet/skillet.lock` (for example commit SHA and/or ETag) so `skillet sync` can detect moving-ref updates.
  - Backward-compatible lock schema update.
  - Detect moving-ref updates without editing `.skillet/config/sources.json`.
  - Preserve no-fetch optimization for pinned immutable refs.
  - Add tests for `@main`, owner/repo default-ref behavior, and pinned commit refs.
- [ ] Default Skillet commands to local project scope unless `--global` (or `-g`) is explicitly specified.
