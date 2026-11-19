# Pull Request Review Instructions

Review Pull Requests for this repository with high-signal, line-anchored feedback focused on correctness, architecture, efficiency, and security.

## Areas of Focus
1. **Repository Rules & Architecture**: Enforce all project rules and styleguides appended below these instructions. Treat layer or boundary breaches as real findings.
2. **Correctness & Edge Cases**: Flag unhandled runtime errors, silent failures, broken state transitions, missing validation, and uncovered edge cases.
3. **Efficiency**: Catch N+1 query patterns, unnecessary I/O on hot paths, and avoidable client-side main-thread work.
4. **Security**: Check for missing authentication/CSRF/permission checks, injection risks, secret or PII leaks, and unsafe defaults.

## What to Ignore
- **Formatting & Linting**: Spacing, line length, quotes, and import ordering enforced automatically by CI linters and formatters.
- **Subjective Style Nits**: Alternative phrasings where the author's code is already clear, idiomatic, and compliant with rules.
- **Untouched Code**: Comment strictly on lines added or modified in the diff (or directly impacted neighbours).

## Formatting
- Point every finding to a specific file and line in the annotated diff, explaining the issue in 1 to 3 concise sentences.
- Provide a GitHub ````suggestion` block whenever a direct code replacement applies.
- If no significant issues exist, return an empty comments list and a single factual summary sentence.
