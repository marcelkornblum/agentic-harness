---
name: architecture-review
description: >-
  Use to perform a strictly read-only architectural and design-smell review across a diff, subsystem directory, or specification (leaky abstractions, coupling, cohesion, and contract fit).
---

# Architecture Review Workflow

Operate under [interaction.md](../../rules/interaction.md) and state your current workflow step at the start of every turn. This skill is **strictly read-only**: never modify files during an architecture review.

## Workflow
1. **Boundary & Context Map**: Identify the review target (a `git diff` range, subsystem directory, or specification) and read surrounding module interfaces and active workspace architecture rules (`.agents/rules/`, `conductor/code_styleguides/`) to understand intended domain seams.
2. **Four-Lens Structural Audit**:
   - **Leaky Abstractions & Seam Breaches**: Callers depending on internal storage, transport, ORM, HTTP, or DOM details; wrong-direction layer imports; pass-through middlemen that obscure ownership.
   - **Coupling & Cohesion Smells**: Shotgun surgery (one domain change forcing edits across scattered modules), feature envy, god classes/modules, catch-all `utils`/`helpers` modules, hidden temporal coupling, or disconnected parallel constants/lists.
   - **Abstraction Calibration**: Speculative generalisation or premature variants violating YAGNI versus duplicated domain policy lacking a shared seam; lingering backwards-compatible shims, re-exports, or wrapper functions.
   - **Contract Ergonomics**: Conflated orthogonal parameters (such as mixing sizing or state into `variant`), ambiguous refusal/error contracts, or hidden global state mutations.
3. **Report Findings & Options**: Output findings only, grouped by severity (`Critical`, `High`, `Medium`, `Low`) in a conversation artifact when above 2 to 3 items, or in a single line in chat if clean (zero pass-checklists). For each finding, cite the exact file/symbol seams and state concrete refactoring options with their trade-offs so the user can decide next steps.
