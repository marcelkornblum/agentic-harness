---
name: conductor-review
description: >-
  Runs end-of-track code-review and architecture-review audits, verifies spec compliance and canonical doc synchronisation, manages initiative-scoped archival, and hands off to Git delivery.
---

# Conductor Review

State your current workflow step at the start of every turn. Scrutinise correctness, test coverage, architectural boundaries, and technical debt without filler praise.

## 1. End-of-Track `code-review` & `architecture-review`
1. Read `conductor/tracks/<track_folder>/spec.md`, `plan.md`, and `conductor/workflow.md`, confirming every acceptance criterion and task checkbox (`[x]`).
2. Execute the `code-review` skill (Mode A local diff review) across the full track change set against active workspace and global rules.
3. Execute the `architecture-review` skill across the track's touched modules and boundaries to check for leaky abstractions, coupling/cohesion smells, YAGNI breaches, or contract issues.
4. Present combined findings grouped by severity. After obtaining user confirmation on any proposed fixes or structural changes, apply approved updates and verify `<task-runner-check>` and `<task-runner-test>` pass.

## 2. Documentation Synchronisation & Registry Completion
1. Check whether `conductor/product.md`, `conductor/tech-stack.md`, or canonical docs in `docs/` need updates to reflect the completed track; propose and apply holistic canonical rewrites (`writing-and-docs.md`) after user confirmation.
2. Set `"status": "completed"` in `conductor/tracks/<track_folder>/metadata.json`, mark the track `[x]` in `conductor/tracks.md`, and report any downstream tracks whose `"depends_on"` list is now unblocked.

## 3. Initiative-Scoped Archival
Inspect `"initiative"` in `metadata.json`:
- **Active initiative with incomplete sibling tracks**: Leave the track folder in `conductor/tracks/` marked `[x]` so relative links and `depends_on` references remain intact.
- **Final track completing an entire initiative**: Reconcile any architecture or runbook docs in `conductor/initiatives/<name>/` and promote them into permanent `docs/` homes (rewriting holistically). Ask whether to move `conductor/initiatives/<name>/` to `conductor/archive/initiatives/<name>/` and all `<name>_*` tracks to `conductor/archive/tracks/`, updating `conductor/tracks.md` if approved.
- **Standalone track (`"initiative": null`)**: Ask whether to archive the track folder to `conductor/archive/tracks/<track_folder>/` and update `conductor/tracks.md`.

## 4. Delivery Handoff
Follow the Git delivery protocol defined in `conductor/workflow.md` (e.g. prompting to confirm the single Gerrit commit after checking staged vs unstaged files, or invoking `complete-work` for GitHub PR delivery).
