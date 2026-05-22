---
name: prep-branch
description: >
  Use to set up the Git branch before commencing coding on a small task or a new phase of a larger plan.
---

# Instructions

Ensure version control hygiene before coding begins. Always state your current workflow step at the start of every response.

## Core Workflow
1. **Identify Work**: State the issue or specific phase you are picking up.
2. **Branch Creation**: 
    - Create a new branch for the work.
    - **Crucial**: If you are in a phased plan and proceeding to a subsequent phase, you MUST create the new branch chained from (based on) the branch of the previous phase.
    - If in doubt about what to use as the base branch, ask the user for clarification.
3. **Proceed**: Once the branch is checked out, immediately activate the `execute-tdd` skill (via `activate_skill(name="execute-tdd")`).
