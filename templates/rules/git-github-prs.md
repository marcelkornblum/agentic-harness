---
trigger: always_on
---

# Operational Tooling & GitHub PR Discipline

- **Task Runner & IDE Edits**: Make file edits with native IDE tools and run formatting, linting, type-checking, and tests through `<task-runner>` commands.
- **Strict `main` Branch Protection**: Never commit or push directly to `main`. Perform all work on an isolated feature or stacked branch and push with explicit refspecs (`git push -u origin <branch>:<branch>`).
- **Visual PR Screenshots**: When a Pull Request alters templates, CSS, components, layouts, or theming with visible UI impact, capture deterministic **Before (`origin/<base>`)** and **After (`HEAD`)** Playwright screenshots outside the working tree and attach a `### Before & After Screenshots` comparison table to the PR description without committing temporary image binaries onto the feature branch.
