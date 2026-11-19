---
trigger: model_decision
description: When creating, editing, or reviewing CSS stylesheets, layout primitives, or design tokens
---

# CSS Architecture: CUBE Layers, Every Layout & 3-Tier Tokens

## 1. CUBE Cascade Layers
Organise all vanilla `.css` stylesheets into explicit cascade layers:
```css
@layer reset, tokens, global, composition, blocks, utilities;
```
- `reset`: Baseline browser resets.
- `tokens`: Design token definitions (`literal.css` and `semantic.css`).
- `global`: Base document defaults.
- `composition`: Intrinsic **Every Layout** primitives (`<l-stack>`, `<l-cluster>`, `<l-sidebar>`, `<l-switcher>`, `<l-box>`, `<l-center>`, `<l-cover>`, `<l-frame>`, `<l-grid>`, `<l-reel>`, `<l-imposter>`; use `.l-*` classes only when a semantic host tag like `<nav>` or `<ul>` is required).
- `blocks`: Component-scoped stylesheets (`<name>.css`).
- `utilities`: Compositional helpers used sparingly (never 1-to-1 atomic utilities).

## 2. Component Encapsulation & Selector Rules
- **Zero Leakage**: Stop component styles strictly at the component root. Never pierce a child component's internal DOM from a parent stylesheet, and never set outer margins on a component root (`margin: 0`; parent layout primitives own spacing).
- **Selectors & Quotes**: Nest pseudo-classes and internal descendants with `&` (max depth 3), keeping variant colours intact across `:hover`, `:active`, and `:focus-visible`. Use single quotes in CSS attribute selectors (`[data-variant='primary']`) and double quotes in HTML attributes.

## 3. Five-Group Property Order
Group declarations in every rule in this exact order without section comments:
1. **Positioning**: `position`, `inset*`, `top`, `right`, `bottom`, `left`, `z-index`.
2. **Display & Box Model**: `display`, `flex*`, `grid*`, `gap`, `align-items`, `justify-content`, `order`, `box-sizing`, `width`/`inline-size`, `height`/`block-size`, `margin*`, `padding*`, `border*`, `outline`, `overflow*`, `contain`.
3. **Colour & Visuals**: `color`, `background*`, `box-shadow`, `opacity`, `visibility`.
4. **Typography**: `font*`, `line-height`, `letter-spacing`, `text-*`, `white-space`, `tab-size`.
5. **Other**: `cursor`, `transition*`, `animation`, `transform`, `pointer-events`, `appearance`, `user-select`.

## 4. Three-Tier Design Tokens
Never hardcode raw colours or magic numbers in components or layouts, and never write cyclic variables (`--x: var(--x, ...)`):
1. **Tier 1 Literals (`--_<sys>-*`)**: Private palette/scale values defined exclusively on `:root` in `tokens/literal.css`; referenced only by Tier 2 semantic mappings and root dark-theme overrides.
2. **Tier 2 Semantic (`--<sys>-*`)**: Public theming API defined on `:root` and aliased on `[data-surface='...']` selectors in `tokens/semantic.css` (surfaces alias `:root` Tier 2 tokens, never Tier 1 literals). Consumed directly by layouts and `<l-*>` primitives.
3. **Tier 3 Component-Local (`--_<component>-*`)**: Private variables declared at the top of `<name>.css` on the component root, mapped exclusively from Tier 2 tokens. Component declarations read only their own `--_<component>-*` variables.
