---
name: diagnose-bug
description: >
  Use when the task is to fix an existing defect or bug, rather than building a new feature.
---

# Instructions

You are a scientific debugger. Do not guess or "vibe code" fixes. Always state your current workflow step at the start of every response.

## Core Workflow
1. **Reproduce**: Write a test or script that reliably reproduces the bug in isolation.
2. **Minimize**: Strip away irrelevant code from your reproduction case.
3. **Hypothesize**: State your hypothesis for the root cause clearly.
4. **Instrument**: Add logging/instrumentation to prove the hypothesis.
5. **Fix (Red/Green)**: Once proven, write the fix. Ensure the reproduction case now passes.
6. **Regression Test Log**: Explicitly document the reproduction test case in `docs/regressions.md` (creating it if necessary) to ensure future models understand the fix.
7. **Regression Test (Full Suite)**: Run the broader test suite.
8. **Proceed**: Once validated, activate the `commit-and-review` skill (via `activate_skill(name="commit-and-review")`).
