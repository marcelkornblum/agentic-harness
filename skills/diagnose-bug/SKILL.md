---
name: diagnose-bug
description: >-
  Use when diagnosing and fixing an existing defect or regression rather than building a new feature.
---

# Scientific Bug Diagnosis

Operate as a scientific debugger: never guess or trial random fixes. State your current workflow step at the start of every turn.

## Workflow
1. **Reproduce**: Write an isolated test or minimal script that reliably triggers the defect, and run it via the repository's task runner to confirm failure.
2. **Minimise**: Strip away unrelated setup until only the smallest failing reproduction remains.
3. **Hypothesise**: State a clear, falsifiable hypothesis for the root cause.
4. **Prove**: Verify the hypothesis through targeted inspection, logging, or instrumentation before changing production logic. Remove temporary instrumentation once proven.
5. **Fix (Red/Green)**: Apply the minimal fix complying with active workspace and global rules ( confirming first if the fix requires altering a public contract or schema), and verify the reproduction test passes.
6. **Regression Check**: Run the broader test and lint suite via the repository's task runner and report the outcome concisely.
