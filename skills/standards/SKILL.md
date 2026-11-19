---
name: standards
description: >-
  Use before committing or delivering work to audit touched code and tests against active coding rules, apply safe internal cleanups, and verify checks pass.
---

# Standards Cleanup Workflow

Operate under [interaction.md](../../rules/interaction.md) and state your current workflow step at the start of every turn.

## Workflow
1. **Scope Assessment**: Inspect the targeted implementation and test files (or current `git status` / `git diff` scope) to understand intended behaviour and boundaries.
2. **Standards Audit**: Evaluate changes against all active workspace rules (`.agents/rules/`, `AGENTS.md`, `GEMINI.md`, `conductor/code_styleguides/`) first, plus global baseline rules ([coding.md](../../rules/coding.md) and matching language files). Read applicable workspace rule files directly.
3. **Hybrid Cleanup**:
   - Apply safe, internal mechanical cleanups (naming, guard clauses, dead code removal, internal type annotations, test assertions, docstring/comment compliance) directly via IDE edit tools.
   - **Halt and report** rather than unilaterally editing whenever a fix alters public APIs, component parameters, database/block schemas, method signatures, or architectural boundaries.
4. **Verification**: Run formatting, linting, type-checking, and test suites using the repository's task runner, fixing any regressions introduced by internal cleanups.
5. **Report**: Output remaining non-mechanical findings only, grouped by severity (in a conversation artifact if more than 2 to 3 items, or a single line in chat if clean; zero pass-checklists).
