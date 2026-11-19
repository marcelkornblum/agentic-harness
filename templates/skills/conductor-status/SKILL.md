---
name: conductor-status
description: >-
  Reports programme progress across Conductor initiatives, active in-progress tracks, unblocked ready tracks, and dependency-blocked tracks.
---

# Conductor Status

Read `conductor/tracks.md` and track `metadata.json` files directly; never stage or commit files.

## Status Protocol
1. Parse `conductor/tracks.md` for all initiatives, standalone tracks, and checkbox states (`[x]`, `[~]`, `[ ]`).
2. Read `conductor/tracks/<track_folder>/metadata.json` for every `[ ]` and `[~]` track to inspect `"phase"` and `"depends_on"`, and read `plan.md` for any `[~]` track to locate the active phase and task.
3. Classify `[ ]` tracks as **Ready** (all `"depends_on"` entries marked `[x]` in `tracks.md`) or **Blocked** (waiting on incomplete `"depends_on"` entries).
4. Present a concise summary covering:
   - **Programme Summary**: Completed vs total tracks per Initiative and Standalone group.
   - **Active (`[~]`)**: Current track, phase, and task.
   - **Ready Queue**: Unblocked `[ ]` tracks ordered by Initiative and Phase.
   - **Blocked Queue**: Pending `[ ]` tracks and the upstream tracks they await.
