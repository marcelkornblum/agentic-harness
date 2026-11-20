---
trigger: model_decision
description: When writing, refactoring, or reviewing application code or automated tests
---

# General Coding Standards

Workspace rules take precedence wherever a project defines its own conventions for these topics.

## Naming Conventions
- **Outcome-Oriented**: Name variables, attributes, and functions by their outcome or intent rather than their internal representation.
- **Verb-Noun Functions**: Use `verb_noun` names for functions and methods (e.g. `get_user_profile`, `validate_email`).
- **Clarity Over Brevity**: Use descriptive names rather than cryptic abbreviations (save standard terms such as `id` and `url`).

## Pattern Reuse, Scope & Refactoring
- **Idiomatic & Consistent**: Follow idiomatic framework patterns. On non-trivial additions (after request triage), inspect existing codebase patterns and reuse them for consistency.
- **DRY & YAGNI**: Extract genuinely shared logic without premature abstraction. Do not over-build features before they are needed; keep surface area small.
- **No Backwards-Compatible Shims**: Never add compatibility shims, re-exports, alias constants, fallback parameter names, or wrapper functions when renaming, moving, or replacing code. Update every call site directly and delete superseded symbols.
- **No Template Regressions**: Never regenerate an existing file from memory or a generic template. Read the current file in full before rewriting or consolidating it, and check your diff so landed fixes stay intact.

## Logic & Error Handling
- **Low Cognitive Load**: Use guard clauses to handle edge cases and errors early rather than nesting `if/else` blocks. Keep functions small and focused on a single concern.
- **Explicit Failure**: Raise specific custom exceptions early. Never fail silently unless explicitly instructed, documented, and covered by tests.

## Documentation & Comments
- **Intent-Focused Docstrings**: Write docstrings on public modules, classes, and functions that state domain intent, invariants, or non-obvious side effects without dryly repeating the symbol name or type signature (skip redundant `Args:` / `Returns:` blocks).
- **No Inline Comments**: Do not add inline comments to production code or unit tests; refactor unclear code instead. Flag any rare exception needed for an external quirk to the user.
- **Test Descriptions**: Express unit test intent through descriptive `test_*` names alone. One-line docstrings are permitted on complex integration tests, and inline step comments are permitted in E2E tests to mark user-level interactions.
- **Relative Links**: Use relative file links (`[file](../path/to/file)`) rather than absolute `file://` paths across all repo-committed code comments and markdown files.

## Pre-Review `standards` Pass
- On any non-trivial code edit (skipping only trivial 1-to-2-line JFDI tweaks), run the `standards` cleanup pass across touched files *before* running final formatting, linting, and test checks and handing back for user review.
