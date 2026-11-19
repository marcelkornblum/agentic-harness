# Code Review Criteria

Provide a high-signal, line-anchored code review focused on correctness, rule compliance, runtime efficiency, and security.

## Areas of Focus
1. **Workspace & Language Rules**: Enforce all workspace rules and styleguides first (yielding to workspace conventions where they override global baseline rules). Treat rule and layer-boundary breaches as concrete findings.
2. **Correctness & Edge Cases**: Flag unhandled exceptions, silent failures, race conditions, broken state transitions, missing input validation, and untested boundary conditions.
3. **Idiomatic Stack Usage**: Verify code uses standard, idiomatic framework primitives and clean extension seams rather than ad-hoc workarounds or monkey-patching.
4. **Data, Query & Runtime Efficiency**: Catch N+1 query patterns, missing `select_related` / `prefetch_related` or bulk operations, unnecessary I/O inside render paths, and main-thread or memory bottlenecks.
5. **Security & Safe Defaults**: Flag unauthenticated endpoints, missing CSRF/permission guards, injection vectors, secret or PII exposure in logs/errors, and unsafe defaults.

## What to Ignore
- **Formatter & Linter Noise**: Ignore spacing, line wrapping, quote style, trailing commas, and import sorting handled by automated formatters and linters.
- **Subjective Rewrites**: Do not propose alternative syntax when existing code is clear, idiomatic, and compliant with rules.
- **Untouched Code**: Anchor comments strictly to added or modified lines in the diff (or immediate neighbouring context directly affected by the change).

## Comment Format
- **Line-Anchored & Terse**: Point every finding to an exact file path and new-file line number from the annotated diff, explaining why it matters in 1 to 3 short sentences.
- **Concrete Replacements**: Include a ````suggestion` block (on GitHub PRs) or concise replacement snippet whenever a direct local code fix applies.
- **Zero Fluff**: Do not add praise, pass-checklists, or filler commentary. When no material issues exist, return an empty comments list and a single crisp summary sentence.
