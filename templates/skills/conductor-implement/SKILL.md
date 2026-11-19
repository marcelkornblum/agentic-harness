---
name: conductor-implement
description: >-
  Executes tasks from a Conductor track plan with pre-flight dependency verification against tracks.md, strict TDD, end-of-phase standards cleanup, phase checkpoints, and zero autonomous Git mutations.
---

# Conductor Implement

State your current workflow step at the start of every turn. Never run `git add`, `git reset`, or `git commit` during task or phase execution. Delegate concrete, well-specified sub-steps to `Model: "flash"` subagents (with strict escalation on anything unexpected) where appropriate.

## 1. Track Selection & Pre-Flight Dependency Gate
1. Read `conductor/tracks/<track_folder>/metadata.json`, `conductor/tracks.md`, and `conductor/workflow.md`.
2. Confirm every upstream track listed in `"depends_on"` is marked `[x]` in `conductor/tracks.md`. If any dependency is `[ ]` or `[~]`, halt immediately and report the incomplete upstream tracks.
3. Read `conductor/tracks/<track_folder>/spec.md` and `plan.md`.
4. When starting a new track, update its checkbox in `conductor/tracks.md` to `[~]` and its `metadata.json` `"status"` to `"in_progress"` via IDE edit tools.

## 2. Phase Execution Loop (Red-Green-Refactor)
For each implementation task in the active phase:
1. **Red**: Write failing tests capturing the requirement and run `<task-runner-test>` to confirm expected failure.
2. **Green**: Implement minimal production code until `<task-runner-test>` passes.
3. **Refactor**: Refine clarity and rule compliance while keeping tests green.
4. **Verify**: Run `<task-runner-check>` and `<task-runner-test>` as specified in `conductor/workflow.md`.
5. Mark completed tasks `[x]` in `conductor/tracks/<track_folder>/plan.md` via IDE edit tools.

## 3. End-of-Phase `standards` Pass & Checkpoint Gate
When all implementation tasks in the current phase reach `[x]`:
1. Run the `standards` skill across the files touched in this phase (applying safe internal cleanups, halting on any public contract questions, and re-running `<task-runner-check>` and `<task-runner-test>`), then mark the phase checkpoint task `[x]` in `plan.md`.
2. **Halt immediately** without staging or committing files.
3. Report one short bullet per logical area changed plus verification status, and ask permission to start the next phase (or run `conductor-review` if all phases are complete).
