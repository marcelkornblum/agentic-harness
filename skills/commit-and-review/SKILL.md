---
name: commit-and-review
description: >
  Use when coding is complete, tests pass, and the code needs to be committed and reviewed by the user.
---

# Instructions

Ensure the work is committed cleanly and reviewed before opening a PR. Always state your current workflow step at the start of every response.

## Core Workflow
1. **Self-Audit**: Before committing, run `git diff` and cross-reference the changes against the original detailed plan and passive coding standards. Fix any discrepancies.
2. **Commit**: Create a concise, conventional commit on the current branch containing the verified work.
3. **Summarise**: Present a concise summary of the changes and the commit to the user. Ask if they are happy with the work. Stop and wait.
4. **Handle Rejection**: If the user is not happy, immediately activate the `execute-tdd` skill (via `activate_skill(name="execute-tdd")`) to integrate their feedback and adjust the code.
5. **Proceed**: If the user is happy, immediately activate the `manage-pr` skill (via `activate_skill(name="manage-pr")`).

