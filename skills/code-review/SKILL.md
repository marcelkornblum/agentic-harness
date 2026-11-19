---
name: code-review
description: >-
  Use to run a line-anchored code review on a local or Gerrit Git diff, review and resolve threads on a GitHub Pull Request, or install the automated GitHub Actions PR review workflow.
---

# Code Review Workflow

Operate under [interaction.md](../../rules/interaction.md) and state your current workflow step at the start of every turn. Apply the review criteria in [review-instructions.md](./references/review-instructions.md) alongside active workspace rules.

## Mode Selection
Determine which mode matches the request:

### Mode A: Local or Gerrit Diff Review (Read-Only)
1. Run the helper script to annotate modified hunks with exact new-file line numbers and gather workspace styleguides:
   ```bash
   python3 ~/.gemini/config/plugins/marcel/skills/code-review/scripts/code_review.py prepare-local [--staged | --commit <sha> | --range <base..head>]
   ```
   *(Omit flags to review all uncommitted working-tree changes against `HEAD`.)*
2. Evaluate the annotated hunks against [review-instructions.md](./references/review-instructions.md), the bundled workspace rules, and global baseline rules.
3. Report findings only, grouped by severity (in a conversation artifact above 2 to 3 items, or one line in chat if clean; zero pass-checklists), citing clickable `file://` line links and concrete replacement snippets.

### Mode B: Interactive GitHub Pull Request Review
1. Fetch PR metadata, open prior review threads, line-annotated diff hunks, and workspace rules (uses `GITHUB_TOKEN` or `gh auth token`):
   ```bash
   python3 ~/.gemini/config/plugins/marcel/skills/code-review/scripts/code_review.py prepare-github --pr <number> [--repo <owner/name>] --output /tmp/pr_review_context.json
   ```
2. **Pass 1 (Open Threads)**: For each open thread in `open_threads`, check the diff since the comment's commit and the `HEAD` excerpt to decide whether the issue is resolved (`resolved: true | false`) and draft a concise reply.
3. **Pass 2 (Inline Diff Review)**: Evaluate `files` against [review-instructions.md](./references/review-instructions.md) and active rules, drafting line-anchored inline comments (using ````suggestion` blocks where direct replacements apply).
4. **Preview & Confirm**: Present proposed thread resolutions and inline comments in a conversation artifact and confirm with the user via `ask_question` before posting to GitHub.
5. **Publish**: Write the approved payload (`{"summary": "...", "evaluations": [...], "comments": [...]}`) to a scratch JSON file, run `publish-github`, and remove temporary files:
   ```bash
   python3 ~/.gemini/config/plugins/marcel/skills/code-review/scripts/code_review.py publish-github --pr <number> [--repo <owner/name>] --input <approved-json>
   ```

### Mode C: Install GitHub Actions Automated PR Reviewer
1. Copy [code_review.py](./scripts/code_review.py) to `.github/scripts/code_review.py`, [pr-review.yaml](../../templates/github/pr-review.yaml) to `.github/workflows/pr-review.yaml`, and tailor [review-instructions.md](../../templates/github/review-instructions.md) to `.github/review-instructions.md` (setting `STYLEGUIDES_DIR` in `pr-review.yaml` to match `.agents/rules` or `conductor/code_styleguides`).
2. Remind the user to configure `GEMINI_API_KEY` in the repository's GitHub Actions secrets.
