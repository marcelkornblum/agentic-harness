# Workflow Routing Rule

This rule governs the start of any session or new piece of work.

## Core Workflow
1. **Start Session**: When the user makes a request, thoroughly research the codebase and the request.
2. **Triage**: Categorize the request:
    - **Bug/Defect**: An existing feature is broken.
    - **Big Feature**: A large architectural change or multi-file new feature.
    - **Hybrid Feature**: A feature involving both logic/data changes and UI components.
    - **Small Feature**: An isolated logic change.
    - **UI/Visual**: Purely markup, CSS, or aesthetic changes.
    - **Exploration**: Testing an unknown library or API without aiming for production code.
    - **Documentation**: Creating issues or PRDs based on context.
3. **Routing**:
    - If **Bug**: Activate `diagnose-bug`.
    - If **Big Feature**: Activate `plan-architecture`.
    - If **Hybrid Feature**: Activate `prep-branch` then `execute-tdd` (with the intent to chain to `prototype-ui`).
    - If **Small Feature**: Activate `prep-branch` then `execute-tdd`.
    - If **UI/Visual**: Activate `prep-branch` then `prototype-ui`.
    - If **Exploration**: Activate `spike`.
    - If **Documentation**: Activate `to-issue`.

## Constraints
- Do not skip the research phase.
- Always communicate your triage decision concisely.
