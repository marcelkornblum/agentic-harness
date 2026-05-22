---
name: execute-tdd
description: >
  Use for all coding tasks to enforce a strict red-green-refactor loop.
---

# Instructions

You write test-driven, clean code. You do not comment code unless absolutely necessary.

## Core Workflow
1. **Detailed Plan**: Read the architectural plan (if applicable) and codebase research. Present a highly detailed implementation plan for this specific task. Ask the user for confirmation. Stop and wait.
2. **Handle Rejection**: If the user is not ready to proceed, integrate their feedback into the detailed plan and return to Step 1.
3. **Write Failing Tests (Red)**: Write comprehensive tests covering the happy path and all edge cases. Do not test out-of-the-box functionality.
4. **Write Code (Green)**: Write the implementation code. Run the tests. If tests fail, iterate on the code until they pass.
5. **Refactor (Refactor)**: Edit the passing code to strictly adhere to the coding standards defined in your passive memory (e.g., the language-specific rules linked from this project's root instructions). Ensure you are operating strictly within the `behaviours.md` persona.
6. **Validate**: Ensure all linting and typechecking passes. Use automated tooling to fix issues where possible.
7. **Proceed**: Once the code is clean, typed, and passing tests, immediately activate the `commit-and-review` skill.
