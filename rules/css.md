# CSS Coding Rules

## Rule Structure & Order
- **Consistency**: Maintain a consistent order for properties (e.g., Positioning -> Box Model -> Typography -> Visuals -> Misc).
- **Cleanliness**: Avoid deeply nested selectors. Prefer shallow, performant rules.

## Modularity & Namespacing
- **Namespacing**: Use modular, minimal namespacing (e.g., BEM-lite or scoped CSS). Avoid global style pollution.
- **Minimalism**: Don't over-engineer. Use the simplest CSS that achieves the design.

## Variables & Hard-Coding
- **Semantic Variables**: Use CSS variables (`--var-name`) for theme-related values (colours, spacing, typography).
- **Scoped Variables**: Use local variables within components to handle internal state or variations.
- **Hard-Coding**: Avoid hard-coded magic numbers. If a value is used more than once, it should be a variable.

## Layout & Responsiveness
- **Minimal Breakpoints**: Use fluid layouts (Flexbox, Grid, `clamp()`, `min()`, `max()`) to minimize the need for media queries.
- **Hard-Coded Values**: Avoid fixed widths/heights where possible; prefer content-driven or relative sizing (`ch`, `em`, `rem`, `%`).

## Z-Indexing
- **Management**: Do not use arbitrary large numbers (e.g., `9999`). 
- **Stacking Contexts**: Use local stacking contexts where possible.
- **Centralisation**: Collate global z-index values into a central variable list to prevent "z-index wars".
