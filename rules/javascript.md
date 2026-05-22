# JavaScript Coding Rules

## Performance & Loading
- **Fast Loading**: Minimise main-thread execution during startup. 
- **Snappy UIs**: Prioritise user interactions. Use `requestIdleCallback` for non-critical work and `requestAnimationFrame` for visual updates.
- **Modern Capabilities**: Take full advantage of modern browser APIs (e.g., `IntersectionObserver`, `Web Workers`, `Fetch API`, `Intl`).

## Progressive Enhancement
- **Core Functionality**: Ensure basic functionality works even if complex scripts fail or are disabled.
- **Enhancement**: Layer advanced features on top of a solid, accessible foundation.

## Code Quality
- **Clarity**: Write readable code over "clever" code.
- **Asynchrony**: Use `async/await` for all asynchronous operations. Handle errors gracefully with `try/catch`.
- **Modularity**: Use ES Modules. Keep functions small and focused on a single concern.
- **DOM Interaction**: Minimise DOM thrashing. Use `DocumentFragment` or batch updates where possible.
