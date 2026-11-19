---
name: conductor-new-track
description: >-
  Plans a new Conductor track (feature, bug fix, or chore), classifies initiative membership and upstream track dependencies, graduates backlog items, and writes spec/plan artifacts without autonomous Git commits.
---

# Conductor New Track

State your current workflow step at the start of every turn. Follow `interaction.md` (one topic at a time, context before `ask_question`, zero unilateral decisions) and `writing-and-docs.md` (target-state purity, exemplar-only snippets). Never run `git add`, `git reset`, or `git commit` when creating track files.

## 1. Context Initialisation
1. Read `conductor/index.md`, `conductor/product.md`, `conductor/tech-stack.md`, `conductor/workflow.md`, and `conductor/tracks.md`.
2. When graduating an item from `conductor/backlog.md`, read `conductor/backlog.md` to extract its context.

## 2. Initiative & Dependency Classification
1. Ask whether the track joins an existing Initiative (`conductor/initiatives/<name>/`), starts a new Initiative, or stands alone.
   - When starting a new Initiative, scaffold `conductor/initiatives/<name>/index.md` (recording overview and any target architecture docs to promote to `docs/` at closure) and add `## Initiative: <Title> (<name>)` to `conductor/tracks.md`.
2. Assign a two-digit sequence number `<NN>` and rollout `phase` integer if part of an Initiative, and identify any upstream track folder names for `"depends_on"`.

## 3. Interrogation, `spec.md` & `plan.md`
1. Interrogate ambiguities, edge cases, and architectural boundaries one topic at a time until requirements are settled.
2. Draft `spec.md` (goal context, declarative requirements, acceptance criteria; label any illustrative code as non-binding exemplars) and obtain user confirmation.
3. Draft `plan.md` structured into TDD phases matching `conductor/workflow.md` (`Red`, `Green`, `Refactor`, quality checks via the repo's task runner, and `- [ ] Task: Phase Standards Cleanup & Checkpoint (run standards skill, then halt)` at each phase boundary) and obtain user confirmation.

## 4. Track Creation & Registry Update
1. Create `conductor/tracks/<initiative>_<NN>_<slug>_<YYYYMMDD>/` (or `conductor/tracks/<slug>_<YYYYMMDD>/` if standalone) containing `spec.md`, `plan.md`, `index.md`, and `metadata.json`:
   ```json
   {
     "type": "feature",
     "status": "new",
     "created_at": "<ISO-8601>",
     "updated_at": "<ISO-8601>",
     "initiative": "<initiative_name or null>",
     "phase": 1,
     "depends_on": []
   }
   ```
2. Add `- [ ] **Track: <Title>** *Link: [./tracks/<track_folder>/index.md](./tracks/<track_folder>/index.md)*` under the matching section in `conductor/tracks.md`, and remove any graduated entry from `conductor/backlog.md`.
3. Report the created files without staging or committing, and ask whether to begin `conductor-implement`.
