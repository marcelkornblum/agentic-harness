# Operational Workflow: Spec-Driven Development

## Core Principles
- **Test-Driven Development**: Execute every feature or bug fix in a Red-Green-Refactor loop.
- **Task Orchestration**: Run formatting, linting, type-checking, and test suites through `<task-runner-check>` and `<task-runner-test>`.
- **End-of-Phase Standards & Checkpoints**: At the end of every phase in `plan.md`, run the `standards` skill across touched files, re-verify checks, and halt immediately for user review before starting the next phase.
- **End-of-Track Dual Review**: When all phases complete, `conductor-review` runs both `code-review` (line-anchored diff review) and `architecture-review` (read-only structural/smell audit) across the full track change set before doc synchronisation, archival, and delivery.
- **Git & Delivery Discipline**: Never run `git add`, `git reset`, or `git commit` autonomously during planning or task execution. Follow `<git-delivery-mode>` (either a single end-of-track Gerrit commit with user-owned staging, or GitHub branch/PR delivery via `complete-work`).

## Programme Management

### Initiatives (`conductor/initiatives/<name>/`)
- Multi-track programmes live under `conductor/initiatives/<name>/index.md` alongside in-flight design or runbook docs destined for `docs/` at initiative closure.
- Initiative tracks use `<initiative>_<NN>_<slug>_<YYYYMMDD>` directory names so alphabetical order matches execution sequence, grouped under `## Initiative: <Title> (<name>)` headings in `conductor/tracks.md`.

### Track Metadata (`metadata.json`)
Track `metadata.json` files include `"initiative"` (`string | null`), `"phase"` (`integer | null`), and `"depends_on"` (`list[string]` of upstream track folder names that must reach `[x]` in `conductor/tracks.md` before implementation starts).

### Backlog (`conductor/backlog.md`)
`conductor/backlog.md` captures unscheduled ideas and technical debt. Items are never referenced in `"depends_on"` until graduated into a formal track in `conductor/tracks/`.

### Archival Discipline
- Keep completed `[x]` tracks belonging to an active initiative in `conductor/tracks/` until all sibling tracks in that initiative finish.
- At initiative closure, holistically fold target architecture docs into `docs/` and move `conductor/initiatives/<name>/` and its tracks into `conductor/archive/{initiatives,tracks}/`.
- Standalone tracks (`"initiative": null`) may move to `conductor/archive/tracks/` immediately upon completion.
