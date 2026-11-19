---
name: complete-work
description: >-
  Orchestrates delivering work into a GitHub Pull Request: enforces main-branch safety, detects existing vs new or stacked PRs, runs standards cleanup and checks, opens or updates the PR, attaches before/after UI screenshots when needed, and resolves CI/review feedback until green.
---

# Complete Work (GitHub PR Delivery)

State your current workflow step at the start of every turn. Print concise context in chat immediately before every `ask_question` prompt, and follow `writing-and-docs.md` for all commit and PR descriptions.

## 1. Branch & PR State Detection
Never commit or push directly to `main`. Inspect current state:
```bash
git branch --show-current
gh pr view --json number,title,baseRefName,headRefName,isDraft,state 2>/dev/null || true
```
- **Existing open PR on current branch**: Record `BASE_REF = baseRefName` and proceed directly to Step 2.
- **Currently on `main`**: Print context and ask via `ask_question` whether to cut a clean branch off `origin/main` or stack onto an active branch, create the branch (`git fetch origin <base> && git checkout -b <branch> origin/<base>`), then ask whether to open as a **Draft PR** or **Ready for Review PR**.
- **On a feature branch with no open PR**: Confirm the intended `BASE_REF` (`main` vs parent stacked branch) and Draft vs Ready preference via `ask_question`.

## 2. Quality Gates, Standards Cleanup & Commit
1. Run `<task-runner-check>` and `<task-runner-test>`, fixing any failures.
2. Execute the `standards` skill across `origin/${BASE_REF}...HEAD` (auto-applying safe internal cleanups and halting to confirm any public contract changes), then re-verify checks.
3. Confirm staged vs unstaged files (`git status -s`) before committing changes onto the feature branch using an imperative subject and 72-char wrapped body.

## 3. Push, PR Creation & Visual Screenshots
1. Push with an explicit refspec (`git push -u origin <branch>:<branch>`).
2. Create (`gh pr create --base "${BASE_REF}" --head "<branch>" [--draft] ...`) or update the PR.
3. If the PR alters templates, CSS, components, layouts, or theming with visible UI impact, capture deterministic **Before (`origin/${BASE_REF}`)** and **After (`HEAD`)** Playwright screenshots in a scratch directory outside the working tree, upload them to the repository's `pr-assets` branch (if configured), and embed a `### Before & After Screenshots` table in the PR body.

## 4. CI & Remote Review Loop
1. Watch CI checks (`gh pr checks --watch`) and trigger automated PR review if configured (e.g. `gh pr comment <pr_number> --body "/review"` on draft PRs).
2. Inspect unresolved review comments and failed checks; apply fixes, re-run `<task-runner-check>` and `<task-runner-test>`, commit, push, and resolve addressed threads until CI is green and no unresolved automated review items remain.
3. Report the PR URL and final verification status concisely.
