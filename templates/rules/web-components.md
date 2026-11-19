---
trigger: model_decision
description: When creating, editing, or reviewing client-side Web Components, page managers, or Vitest DOM specs
---

# Light DOM Web Components & Page Mediators

## 1. Custom Element Boundaries
- **Light DOM Enhancement**: Subclass native `HTMLElement` in Light DOM (never `attachShadow`), enhancing server-rendered HTML in place. Use a custom element root tag only when client-side JS behaviour is required; keep purely static components on semantic HTML tags.
- **Subtree Encapsulation**: Query and mutate strictly within `this.querySelector` / `this.querySelectorAll`; never reach outside the component via `document.querySelector` for sibling or parent state, and never pierce a child custom element's internal DOM from a parent.
- **Orchestration**: Expose explicit public methods on child custom elements for downward calls (e.g. `dialog.open()`, `popout.selectValue(val)`) and dispatch bubbling `CustomEvent`s upward. Cross iframe boundaries exclusively via `postMessage`, never by mutating `contentDocument`.

## 2. Page Mediators & Idempotent Lifecycle
- **Zero Global Side-Effects in Components**: Reusable element and composite classes must never touch `localStorage`, `sessionStorage`, `document.cookie`, or `window.location.href`, nor bind global `document` keyboard shortcuts. Delegate persistence, URL state, and cross-component coordination to page-level mediator modules.
- **Lifecycle Cleanup**: Keep `connectedCallback()` idempotent and abort an instance `AbortController` in `disconnectedCallback()` to tear down all listeners, timers, observers, and requests cleanly.
- **Module Specifiers**: When shipping bundler-free TypeScript output, include explicit `.js` extensions on relative imports (`import { Foo } from './foo.js';`).

## 3. Co-located Behavioural Testing
- Test custom elements and page mediators behaviourally in co-located `<name>.spec.ts` files beside `<name>.ts` using Vitest (`happy-dom`), asserting on real DOM state, ARIA attributes, emitted `CustomEvent` payloads, and `AbortController` teardown.
