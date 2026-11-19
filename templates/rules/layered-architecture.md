---
trigger: model_decision
description: When writing, refactoring, or reviewing Python/Django backend layers, models, services, business logic, or factories
---

# Layered Backend Architecture

## 1. Four-Layer Responsibility Split
- **Interfaces** (views, API endpoints, management commands, tasks, template tags, signal receivers): Parse input, call business logic, and format responses. Hold zero business rules or `_`-prefixed helper functions (beyond framework hooks); place helpers in the domain module they serve. Do not create catch-all `utils.py` or `helpers.py` modules.
- **Business Logic** (`<app>/business_logic/<area>.py`):
  - **Rules** (`can_...`, `is_...`, `has_...`): Side-effect-free functions returning `bool` or a filtered collection. Feature-flag and settings checks live here.
  - **Processes** (`submit_...`, `publish_...`): Enforce relevant rules, wrap writes in `transaction.atomic()`, call services, and schedule side effects (notifications, emails, tasks) via `transaction.on_commit()`. Make refusals explicit in return types/docstrings or custom exceptions.
- **Services** (`<app>/services/<area>.py`): Read and mutate data for their own app (`get_`, `create_`, `update_`, `delete_`, `build_`) or wrap one external integration. Enforce data-integrity invariants via custom exceptions and own query efficiency (`select_related`, `prefetch_related`, bulk operations, zero N+1). Hold zero authorisation policy.
- **Data** (models, managers, querysets): Thin field, relationship, simple derived property, and queryset filter definitions. Every Django model must have a `factory_boy` factory exposing traits/sub-factories covering valid model states.

## 2. Dependency Direction & Signatures
- **One-Way Imports**: `Interfaces -> Business logic -> Services -> Data` (interfaces may call read-only services directly only for trivial reads; trusted callers such as migrations, CLI commands, and tests may call services directly). Neither business logic nor services may reference HTTP objects (`request`, `HttpResponse`, `PermissionDenied`). Never import Django models outside services and tests.
- **Area Naming & Aliases**: Mirror `<area>.py` names across `business_logic/` and `services/`, importing them with layer aliases (`from app.services import orders as orders_service`).
- **Signatures**: Annotate every function in `business_logic/` and `services/` with precise types (`QuerySet[Order]`, `Sequence[OrderItem]`, `Order | None`; never unexplained `Any`). Public functions in both layers must require keyword-only arguments (`*`) and prefer bulk `Sequence[...]` / `Iterable[...]` inputs over single-item loops.

## 3. Layer Testing
- **Rules**: Unit-test every rule branch and edge case (`tests/business_logic/test_<area>.py`).
- **Processes**: Test that every refusal path blocks execution and every allowed path invokes expected services and side effects.
- **Services**: Test data mutations and integrity exceptions (`tests/services/test_<area>.py`).
- **Interfaces**: Cover allowed and refused end-to-end request paths concisely.
