---
trigger: model_decision
description: When writing, refactoring, or reviewing HTML templates or CSS/SCSS stylesheets
---

# HTML & CSS Baseline Rules

Workspace rules take precedence wherever a project defines its own HTML or CSS conventions.

## HTML Semantics & Accessibility
- **Semantic Elements**: Use native HTML5 elements for their intended purpose (`<main>`, `<nav>`, `<article>`, `<section>`, `<button>` for actions, `<a>` for navigation). Keep markup lean without redundant wrapper elements.
- **Syntax & Separation**: Use lowercase tag and attribute names with quoted values. Keep structure in HTML, presentation in CSS, and behaviour in scripts.
- **Accessibility**: Prefer native semantics over ARIA; add ARIA attributes only where required. Provide meaningful `alt` text on images, maintain logical heading order, and keep interactive elements keyboard-navigable with clear focus states.

## CSS Cascade, Selectors & Sizing
- **Cascade & Nesting**: Organise stylesheets with native `@layer`. Use native `&` nesting (up to 3 levels deep) for states and internal descendants, preserving variant colours across `:hover`, `:active`, and `:focus-visible` states.
- **Selector Hygiene**: Do not use BEM (`__`, `--`), `!important`, `#id` selectors, or 1-to-1 atomic utility classes. Express component variants and interactive states via `[data-*]` and `[aria-*]` attributes.
- **Variables, Fluidity & Stacking**: Use CSS custom properties instead of repeated magic values. Prefer local stacking contexts and central `z-index` tokens over arbitrary large `z-index` numbers. Favour fluid layout sizing (`flex`, `grid`, `clamp()`, `min()`, `max()`, relative units) over fixed pixel dimensions.
