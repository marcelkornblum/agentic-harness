---
trigger: model_decision
description: When drafting or editing documentation, READMEs, architecture/concept guides, specs, plans, commit messages, or PR/CL descriptions
---

# Writing, Documentation & Commit Style

## 1. Target-State Purity & Canonicity
- **Positive Target State Only**: Describe only what the system or plan is. Never include conversational history, rejected options, or negative statements explaining why an omitted idea was left out.
- **No Shadow Catalogues**: Teach concepts and invariants with 1 to 2 examples and relative links to source files; never maintain exhaustive inventory lists or tables that duplicate code.
- **Holistic Canonical Rewrites**: When folding spec changes into repo docs, re-read the whole section and rewrite it so the document speaks with a single timeless voice rather than bolting on additive patches.
- **Genre-Matched Rationale**: Keep agent rules, skills, task plans, and runbooks imperative/declarative (adding a brief parenthetical reason only where a constraint would otherwise look arbitrary). Include problem forces, invariants, and trade-offs in human architecture, RFC, and `concepts/` docs. Give brief goal context plus declarative requirements in transient feature specs.
- **Exemplars Over Premature Contracts**: Keep specs and plans at intent and boundary level; label illustrative code snippets or sketched signatures explicitly as non-binding exemplars so downstream execution and review do not treat early sketches as rigid contracts.

## 2. Audience, Prose Craft & Markdown Structure
- **Audience**: Unless writing agent-specific instructions, write for smart, senior developers who already know the language, frameworks, and tooling ecosystem, yet are new to this codebase. Explain project-specific mental models, boundaries, and invariants; never explain standard language or framework features.
- **Top-Down & Non-Repetitive**: Move from high-level mental model down to granular detail; never repeat mechanics already obvious from code.
- **Register & Voice**: In human docs, use plain Germanic words (`use`, `keep`, `split`, `before`, `check`) and warm `you` / `we` phrasing rather than stiff Latinate diction. In agent-facing docs, use dry, compressed prose.
- **Sentence Rhythm & Punctuation**: Keep sentences shortish, pairing crisp 8-to-12-word lead sentences with 15-to-22-word explanations. Prefer brackets `(...)` and semi-colons `;` over em-dashes.
- **Cut LLM Tics**: Avoid promotional adjectives (*robust, seamless, comprehensive, clean, flexible, lightweight*), trailing `-ing` participial clauses (*"...ensuring X and preventing Y"*), nominalisations (*"performs validation of"* -> *"validates"*), and throat-clearing openers (*"At its core"*, *"It is worth noting"*).
- **Structure by Purpose**: Use cohesive paragraphs in *"how things work"* architecture docs, and a conceptual lead plus terse bullets in *"how to do things"* guides. Hold human docs to a calm structural baseline (code tokens anchoring lists, spending bold labels or quote blocks sparingly across a full page rather than in every section).
- **Links & Diagrams**: Use relative links in all repo-committed markdown files (reserving clickable `file://` links for chat and conversation artifacts). Prefer a clear sentence to a diagram; when non-linear topology genuinely benefits from a diagram, use portable ASCII art no wider than 60 characters.

## 3. Commit Messages & PR/CL Descriptions
- Use an imperative subject line and hard-wrap body lines at 72 characters (omitting Conventional Commit prefixes unless required by the repository's own rules).
- Use a single subject line when the change is self-explanatory. Otherwise, open with 1 to 2 short sentences stating *why* the change was made, followed by plain unbolded bullets grouping logical outcomes (no Markdown bolding or quote blocks, no file-by-file diff recaps, no test/lint pass bragging, and no AI checklists). Preserve genuine Git trailers such as `Change-Id`.
