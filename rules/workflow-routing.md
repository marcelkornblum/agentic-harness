# Workflow Routing Rule

This rule governs the start of any session or new piece of work.

## Core Workflow
1. **Start Session**: When the user makes a request, thoroughly research the codebase and the request.
2. **Triage (Big vs Small)**:
    - Assess if the task is a "Big" change (architectural, multi-file, new feature) or a "Small" change (isolated bug fix, single-file edit).
3. **Routing**:
    - If the change is **Big**: Immediately state your assessment and activate the `plan-architecture` skill.
    - If the change is **Small**: Immediately state your assessment and activate the `prep-branch` skill.

## Constraints
- Do not skip the research phase.
- Always communicate your triage decision concisely.
