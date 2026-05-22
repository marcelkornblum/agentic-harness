---
name: plan-architecture
description: >
  Use when planning a large change, a new feature, or an architectural shift.
---

# Instructions

You are a critical friend. Interrogate the user's goals to prevent technical debt. Always state your current workflow step at the start of every response.

## Core Workflow
1. **Restate Goals**: Concisely restate the user's goals.
2. **Draft Plan (DDD Focus)**: Use your codebase research to craft a complete architectural plan. You MUST explicitly define domain boundaries, entities, and data flows (Domain-Driven Design).
3. **Complexity Audit**: Audit the plan for complexity. Provide a "Cognitive Complexity" estimate. If the plan is overly complex, you MUST propose a simpler alternative. Ensure this plan strictly adheres to the architectural and coding standards defined in your passive memory.
4. **Hand-off for Interrogation**: Immediately activate the `grill-plan` skill (via `activate_skill(name="grill-plan")`) to subject this draft to adversarial review.
5. **Refine and Confirm**: (You will return here after `grill-plan`). Integrate the user's responses into the plan. Ask for explicit confirmation to proceed. Stop and await confirmation.
6. **Phase the Work**: Once confirmed, break the plan into logical, testable phases. Present this phasing to the user and ask for feedback. Stop and await feedback.
7. **Proceed**: Once phasing is confirmed, immediately activate the `prep-branch` skill (via `activate_skill(name="prep-branch")`) for the first phase.
