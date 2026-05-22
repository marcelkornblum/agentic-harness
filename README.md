# Agentic Harness

My personal, centralized repository for AI agent skills, instructions, and workflows. This is where I collect my coding best practices and complex workflows so I can reuse them across projects and across different LLM agents (Cursor, Gemini CLI, Cline, etc.) without duplication.

Feel free to crib what's here, but it's built for my specific workflows.

## Structure

- **`/rules`**: Passive knowledge. Markdown files with my specific coding standards, architectural rules, and tone guidelines (e.g., `typescript.md`, `react.md`).
- **`/skills`**: Active knowledge. Self-contained directories following the Agent Skills structure for complex, multi-step tasks.

## How It Works: Progressive Disclosure

This setup keeps agent context lean:
1.  **Project Initialization**: I link a new project to this repo. The agent reads a lightweight instruction file (e.g., `.cursorrules` or `INSTRUCTIONS.md`) in the target project.
2.  **Referencing Rules**: That file tells the agent exactly which rules in this repo it needs to follow for that specific stack.
3.  **Activating Skills**: The agent is pointed to `/skills/` and only pulls in a specific `SKILL.md` when I ask for a task that matches.

## Setup & Usage

To hook these standards into a new project:

1.  Navigate to the target project.
2.  Run the setup script:
    ```bash
    /home/marcel/projects/agentic-harness/setup.sh
    ```
3.  Customize the generated `.cursorrules` to list the specific rules from `/rules/` that apply.

## Creating New Content

- **New Rule**: Drop a `.md` file in `/rules/`.
- **New Skill**: Copy `/skills/_template/` and update `SKILL.md`.

