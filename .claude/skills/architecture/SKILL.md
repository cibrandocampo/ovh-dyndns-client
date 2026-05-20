---
name: architecture
description: Architecture validation before implementing. Use at the start of any feature or fix to verify the approach fits the project structure — before writing a single line of code.
---

# Architecture

Before implementing, answer these questions. If any answer is "no" or "unsure", stop and resolve it with the user.

## Right-Size the Structure First

Not every project needs the same level of layering. Apply the minimum structure that keeps the project clean and maintainable — no more.

| Project type | Appropriate structure |
|---|---|
| Script / utility | Functions in modules. No layers needed. Keep related logic together. |
| Simple CRUD API | Routes → service functions → DB calls. Three logical areas, no formal layers. |
| Mid-size app | Separate business logic from HTTP handlers and DB access. Clear module boundaries. |
| Complex domain | Full layered architecture: Domain / Application / Infrastructure / Interface. |

**The rule**: structure must be chosen at the start and applied consistently — not added later as an afterthought. A simple structure chosen on day one is far better than a complex structure bolted on halfway through.

**The anti-rule**: do not build cathedrals for what is a village chapel. If the project is a simple API, do not introduce domain events, ports & adapters, and abstract repositories. That is overengineering, and it slows everything down.

When in doubt, choose the simpler level. It is always easier to add structure later than to remove it.

---

## Layer Responsibilities (for mid-size and complex projects)

| Layer | Contains | Must NOT contain |
|-------|----------|-----------------|
| **Domain** | Business rules, entities, value objects, domain events | Framework code, DB queries, HTTP logic |
| **Application** | Use cases, orchestration, input/output ports | Business rules, direct DB access, HTTP details |
| **Infrastructure** | DB adapters, HTTP clients, external services, framework glue | Business rules, use case logic |
| **Interface** | Controllers, serializers, views, CLI handlers | Business logic, DB queries |

If you are unsure which layer a piece of code belongs to, ask: "Would this code need to change if I swapped the database? The framework? The transport protocol?" Each layer should only need to change for its own reasons.

## Validation Checklist — Before Implementing

### Placement
- [ ] I know which layer each new class/function belongs to.
- [ ] No business logic is leaking into controllers, serializers, or views.
- [ ] No database queries are happening inside domain entities.
- [ ] No framework imports inside domain or application layer code.

### Reuse
- [ ] I searched the codebase for similar functionality before writing new code.
- [ ] If I found similar code (2+ instances), I am reusing or extracting — not duplicating.
- [ ] The abstraction I am creating (if any) is justified by actual reuse, not speculation.

### Cohesion & Coupling
- [ ] The class/module I am adding or modifying has a single, clear responsibility.
- [ ] I am not adding a method to a class just because it is convenient — it belongs there.
- [ ] New dependencies between modules go in one direction only (inner layers don't depend on outer layers).

### Scope
- [ ] I am not building for hypothetical future requirements (YAGNI).
- [ ] Every abstraction I introduce is needed now, not "might be useful later".
- [ ] If a function would be over 30 lines, I have considered splitting it.

## Red Flags — Stop and Reconsider

If you find yourself doing any of the following, pause and discuss with the user:

- **Fat controllers**: a controller/view doing more than receiving input → calling a use case → returning output.
- **Anemic domain**: entities that are just data bags with no behaviour; all logic lives in services.
- **Service soup**: dozens of service classes with one method each, no clear domain model.
- **Circular dependencies**: module A imports module B which imports module A.
- **Premature abstraction**: an interface or base class with only one implementation.
- **God object**: a class that knows about or orchestrates everything.

## DRY in Practice

The rule is not "never write similar code twice". It is: **duplication of knowledge is the problem, not duplication of text**.

- If two pieces of code look alike but represent different concepts, keep them separate.
- If two pieces of code represent the **same rule or decision**, extract it — one change should update both.
- The right moment to extract is when you are writing the **third** instance, not the second.

## How to Apply

1. Read `CLAUDE.md` and `MEMORY.md` for project-specific patterns before designing.
2. Sketch the layer placement of the new code before writing it.
3. Run through the checklist above.
4. If you identify a red flag, surface it to the user before proceeding — do not paper over it.
5. Document significant architecture decisions in the plan doc or task file.
