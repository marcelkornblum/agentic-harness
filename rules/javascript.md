---
trigger: model_decision
description: When writing, refactoring, or reviewing TypeScript or JavaScript code
---

# TypeScript & JavaScript Baseline Rules

Workspace rules take precedence wherever a project defines its own TypeScript or JavaScript conventions.

## Modules, Typing & Syntax
- **Strict TypeScript & Exports**: Compile cleanly under `strict: true`, `noImplicitAny`, and `strictNullChecks`. Use ES modules with named exports (avoiding `export default` unless required by a framework config).
- **Formatting & Declarations**: Use `const` by default, `let` when reassigned, and never `var`. Require K&R braces on all control blocks, 2-space indentation, semicolons, single quotes for strings (template literals for interpolation), `for..of` loops, strict `===` / `!==` checks, and `async`/`await`.
- **Classes, Naming & Safety**: Use ordinary methods rather than JS `get`/`set` property accessors. Name classes/interfaces in `UpperCamelCase`, methods/variables in `lowerCamelCase`, and constants in `CONSTANT_CASE`. Never use `eval()`, `with`, or built-in prototype mutation.

## Browser Runtime, Performance & Testing
- **Progressive Enhancement & Main Thread**: Keep core journeys working on accessible HTML where applicable, and keep startup/interaction work light (`requestAnimationFrame` for visual updates, `requestIdleCallback` for non-critical work, minimal DOM thrashing), unless overridden by a project's client-app architecture.
- **Lifecycle & Testing**: Clean up event listeners, observers, and in-flight requests via `AbortController` signals. Test DOM behaviour natively in Vitest rather than matching `.ts` source strings from Python test suites.
