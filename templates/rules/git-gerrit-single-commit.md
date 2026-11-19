---
trigger: always_on
---

# Operational Tooling & Gerrit Staging Discipline

- **Task Runner & IDE Edits**: Make file edits with native IDE tools and run formatting, linting, type-checking, and tests through `<task-runner>` commands.
- **Zero Autonomous Git Mutations**: Never stage (`git add`), unstage (`git reset`, `git restore --staged`), or commit files on your own impulse or as an automatic workflow side effect. Execute Git write commands only upon explicit instruction from the user.
- **Staging Index as Review Mirror**: The user stages reviewed files so subsequent unreviewed edits stay isolated in unstaged diffs; never tamper with the staging index.
- **Single-Commit Delivery & Unstaged Clarification**: Do not create intermediate metadata or checkpoint commits; deliver each unit of work as a single cohesive Gerrit Change Request commit at the end of review. If asked to commit while unstaged changes exist, halt and ask whether to commit only staged files or stage specific files first.
