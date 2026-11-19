# Marcel: Antigravity Plugin & Project Scaffolding

This repository packages my personal Antigravity customisations into a global plugin alongside starter templates for new repositories.

Symlinking the repository root into `~/.gemini/config/plugins/marcel` activates the global rules and skills across every workspace automatically, while keeping `templates/` inert until explicitly scaffolded into a project.

```text
agentic-harness/
├── plugin.json     # Global plugin manifest ("marcel")
├── rules/          # Global rules (always_on + model_decision)
├── skills/         # Global skills (e.g. code-review)
└── templates/      # Opt-in project rules, skills & CI
```

## Global Layer (`rules/` & `skills/`)

Global files hold preferences that apply across every session. [interaction.md](./rules/interaction.md) stays active on every turn to govern request triage, `flash` subagent delegation, and Critical Friend behaviour. Other global rules (such as [writing-and-docs.md](./rules/writing-and-docs.md) and baseline language files like [python.md](./rules/python.md)) load on demand via `trigger: model_decision` and yield whenever a workspace defines its own conventions.

Portable workflows in [skills/](./skills/) separate pre-delivery standards cleanup ([standards](./skills/standards/SKILL.md)), line-anchored diff and PR review ([code-review](./skills/code-review/SKILL.md)), and read-only structural design audits ([architecture-review](./skills/architecture-review/SKILL.md)).

## Project Scaffolding (`templates/`)

Architectural choices, component conventions, GitHub Actions PR review pipelines, and Git delivery workflows vary per repository and live under [templates/](./templates/) so they never collide with existing project setups. Run [scaffold-project](./skills/scaffold-project/SKILL.md) to pick, tailor, and install the matching files for a codebase.

## Installation

```bash
ln -s /Users/kornblum/projects/agentic-harness ~/.gemini/config/plugins/marcel
```
