---
name: commit-and-review
description: >
  Use when coding is complete, tests pass, and the code needs to be committed and reviewed by the user.
---

# Instructions

Ensure the work is committed cleanly and reviewed before opening a PR.

## Core Workflow
1. **Commit**: Create a concise, conventional commit on the current branch containing the verified work.
2. **Summarise**: Present a concise summary of the changes and the commit to the user. Ask if they are happy with the work. Stop and wait.
3. **Handle Rejection**: If the user is not happy, immediately activate the `execute-tdd` skill to integrate their feedback and adjust the code.
4. **Proceed**: If the user is happy, immediately activate the `manage-pr` skill.
