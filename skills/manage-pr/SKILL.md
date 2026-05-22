---
name: manage-pr
description: >
  Use to open a Pull Request and manage the transition to the next piece of work.
---

# Instructions

Manage the lifecycle of the PR and coordinate the next phase.

## Core Workflow
1. **Open PR**: Open a Pull Request for the current branch using the project's standard tooling.
2. **Summarise and Prompt**: Summarise the PR link/details for the user. Ask if they wish to proceed to the next piece of work. Stop and wait.
3. **Routing**:
    - If the user says **No**: End the workflow.
    - If the user says **Yes** and you are currently inside a phased architectural plan: Immediately activate the `prep-branch` skill to chain the next branch.
    - If the user says **Yes** but there is no overarching plan: Prompt the user for their next request and refer to the `workflow-routing.md` rule.
