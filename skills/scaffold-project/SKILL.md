---
name: scaffold-project
description: >-
  Use when setting up agent rules, skills, automated GitHub PR reviews, or Conductor workflow scaffolding in a new or existing repository using the templates in this plugin.
---

# Scaffold Project Workflow

State your current workflow step at the start of every turn. Follow [interaction.md](../../rules/interaction.md) throughout (one topic at a time, concise context before `ask_question`, zero unilateral decisions).

## 1. Repository Audit (Read-Only)
1. Inspect the target repository's root manifests (`pyproject.toml`, `package.json`, `justfile`, `Makefile`), Git remote (`git remote -v` for GitHub vs Gerrit), and any existing `.agents/`, `.github/`, `conductor/`, `GEMINI.md`, or `AGENTS.md` files.
2. Read the available template directories under [templates/](../../templates/) (`rules/`, `skills/`, `github/`, and `conductor/`).
3. Summarise the detected stack, task runner, Git host, and existing agent setup concisely.

## 2. One-Topic-at-a-Time Selection
Walk through each applicable category one topic at a time using `ask_question` (with concise chat context printed above):
1. **Architecture & Domain Rules** (`templates/rules/`): Propose matching templates (`layered-architecture.md`, `css-architecture.md`, `web-components.md`, `dj-design-system-components.md`, or `seo-and-structured-data.md`) for `.agents/rules/`.
2. **Git, Delivery & Automated PR Review**: Propose `git-github-prs.md` (+ `complete-work` and the `templates/github/` automated PR review workflow if hosted on GitHub) or `git-gerrit-single-commit.md` based on the Git remote, confirming task-runner commands (`just`, `make`, or package scripts).
3. **Workflow Framework**: Ask whether the project wants the custom Conductor v2 scaffold (`templates/conductor/` + `templates/skills/conductor-*`, including `conductor/initiatives/`, `conductor/tracks/`, and `conductor/backlog.md`) or another workflow setup.

## 3. Tailoring & Confirmation Spec
1. Adapt selected templates to the repository's real paths, package names, and task-runner commands (replacing `<task-runner-check>` / `<task-runner-test>` placeholders with actual repo commands and removing irrelevant sections; when installing GitHub PR review CI, copy [code_review.py](../code-review/scripts/code_review.py) to `.github/scripts/code_review.py`).
2. Present a concise summary of the target file paths and tailored adjustments in a conversation artifact spec, and obtain explicit sign-off before writing any files to the repository.

## 4. Installation
1. Write the approved files into the target repository using IDE file tools (creating empty `.gitkeep` directories for `conductor/initiatives/` and `conductor/tracks/` when Conductor is selected).
2. Leave Git staging untouched and report the installed paths concisely.
