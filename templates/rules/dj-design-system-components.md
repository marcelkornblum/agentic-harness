---
trigger: model_decision
description: When creating, editing, or reviewing dj-design-system UI components, parameter descriptors, component templates, or gallery.py files
---

# `dj-design-system` Component Rules

## 1. Co-location & Granularity
- Co-locate `<name>.py`, `<name>.html`, `<name>.css` (or `.scss`), and `gallery.py` in the component folder, adding `<name>.ts` and `<name>.spec.ts` only when client-side interactivity is needed.
- Do not wrap trivial single HTML tags or plain loops in 1-line components.

## 2. Orthogonal Parameters & Python Boundaries
- **Presentation Only**: Components sit strictly at the presentation boundary; resolve database queries and business logic in services/views before passing data in. Never instantiate or call `.render()` on another component inside Python (compose child components strictly in `<name>.html` via template tags and `{% slot %}` blocks).
- **Parse in `*Param` Descriptors**: Own input cleaning, validation, defaults (`default=None` for optional attributes), and declarative HTML reflection (`attr=True`, `attr="aria-..."`, `data_attr=True`, `attr_style="boolean" | "string"`) on `*Param` descriptors. Keep `get_context()` focused on cross-parameter derivations.
- **Orthogonal `variant` Design**: Reserve `variant` strictly for semantic/visual intent (`primary`, `danger`, `ghost`, `info`). Keep sizing (`size`), typography (`is_code`), and interactive state (`disabled`, `selected`, `pressed`) as separate orthogonal parameters rather than collapsing them into variants.
- **Structured Item DTOs**: When accepting collections of items (tabs, breadcrumbs, options), define a frozen `@dataclass(frozen=True)` in `<name>.py` and re-export it from `__init__.py`.

## 3. Logic-Minimal Templates & Gallery
- **Attribute Reflection (`{{ attrs }}`)**: Render `{{ attrs }}` (or scoped `{{ <param>_attr }}` helpers) on the host/interactive tag instead of writing manual `{% if %}` attribute conditionals. Do not use template filters (`|default`, `|lower`) to compute fallback values or transform data in templates.
- **Gallery & Tests**: Export `config = GalleryConfig(...)` in `gallery.py` covering meaningful visual/interactive states, and unit-test parameter cleaning, `get_context()` derivations, and rendered HTML alongside gallery accessibility checks.
