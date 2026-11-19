---
trigger: model_decision
description: When writing, refactoring, or reviewing Python code or pytest suites
---

# Python Baseline Rules

Workspace rules take precedence wherever a project defines its own Python conventions.

## Structure & Functions
- **Thin Models & Decoupling**: Keep data models thin; put query and business logic in services. Wrap external side-effect libraries in service modules and avoid mutable global state.
- **No HTML in Python**: Never construct raw HTML strings or call `mark_safe()` / `format_html()` in Python modules; templates own markup generation.
- **Scripts & Closures**: Place executable script logic inside `main()` under `if __name__ == "__main__":`. Do not nest `def` functions inside functions except for decorator wrappers; use module-level helpers or `functools.partial`.

## Imports & Naming
- **Imports**: Prefer module-level imports (using local imports only to break circular dependencies). Use standard symbol imports for types, dataclasses, and exceptions, and layer aliases (`from app.services import billing as billing_service`) when importing service or business-logic modules. Never import `_`-prefixed symbols across modules.
- **Naming**: `snake_case` for modules, functions, methods, and variables; `PascalCase` for classes; `ALL_CAPS` for module constants; leading `_` for module- or class-private members.

## Data, Types & Control Flow
- **Call Sites & Defaults**: Supply keyword arguments (`kwargs`) when calling functions. Never use mutable objects (`[]`, `{}`) as default parameter values.
- **Structured Data & Constants**: Pass typed `@dataclass` objects instead of raw dicts. Extract strings referenced more than once into constants, and derive related subsets, bounds, and defaults from a single canonical `Enum` or constant class rather than maintaining parallel lists.
- **Idioms & Typing**: Annotate specific types everywhere (no duck typing or unexplained `Any`). Use implicit falsiness (`if not items:`) for collections and explicit `if value is None:` for `None` checks. Never use bare `except:`. Format strings with `f`-strings and `TODO`s as `TODO(username): ...`.

## Testing
- **Validation & Scope**: Lint, format, and type-check changes via the repository's task runner. Test service happy paths and edge cases exhaustively; do not test OOTB framework behaviour.
- **Fixtures & Assertions**: Co-locate all pytest fixtures in `conftest.py` (never inside `test_*.py` files). Use plain `assert` statements rather than `unittest` `self.assert*` methods.
