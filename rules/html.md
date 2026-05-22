# HTML Coding Rules

## Core Principles
- **Semantic Markup**: Always use the most appropriate HTML element for the job (e.g., `<main>`, `<nav>`, `<article>`, `<section>`). Avoid "div-itis".
- **Accessibility (A11y)**:
    - Use ARIA roles and attributes only when necessary; prefer native semantic elements.
    - Ensure all images have meaningful `alt` text.
    - Use proper heading levels (`<h1>` through `<h6>`) to maintain a logical document outline.
    - Ensure interactive elements are keyboard-navigable and have clear focus states.
- **Conciseness**: Keep markup lean. Avoid redundant attributes and unnecessary wrapper elements.

## SEO & Social Optimization
- **Meta Tags**: Always include standard meta tags for SEO (title, description).
- **Social Rendering**: Include Open Graph (`og:`) and Twitter (`twitter:`) tags to ensure rich rendering in social contexts. Prioritize high-quality image previews.
- **Canonicalization**: Use `<link rel="canonical">` to prevent duplicate content issues.

## AI & Machine Readability
- **Schema.org**: Use JSON-LD or Microdata to provide structured data about the content (e.g., Product, Article, FAQ).
- **Agent Helpers**: Use descriptive `id` and `class` names that provide context to AI agents. 
- **Hidden Context**: If necessary, use `data-*` attributes to provide machine-readable state or metadata that shouldn't be visible to users but is helpful for programmatic interaction.

## Standards
- Use lowercase for all tags and attributes.
- Always quote attribute values.
- Use `lang` attribute on the `<html>` tag.
- Prioritize `button` elements for actions and `a` elements for navigation.
