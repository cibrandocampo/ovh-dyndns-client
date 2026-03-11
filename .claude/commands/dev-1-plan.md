---
description: Plan a new feature — conceptual design, scope, and proposal
argument-hint: <brief description of the feature>
---

# Plan feature: $1

**Goal**: produce a design document approved by the user.
**Behaviour**: you only plan and ask questions. No code, no tasks, no files beyond the plan document itself.

---

## Phase 1 — Understand the goal

1. Read `CLAUDE.md` and `MEMORY.md` for project context.
2. Read `docs/` for existing documentation (ARCHITECTURE.md, configuration.md, etc.).
3. If previous plans exist in `docs/plans/`, read them to understand decisions already made.
4. Ask the user everything needed with `AskUserQuestion`:
   - What problem does this feature solve?
   - What stack layers does it affect? (API, application, domain, infrastructure, tests)
   - Are there open design decisions?
   - Are there constraints or preferences? (e.g.: "no schema changes", "API only")

**Never assume. If anything is unclear, ask with `AskUserQuestion` before continuing. Five questions now beats a full rewrite later.**

**Do not advance to Phase 2 until you have clear answers.**

---

## Phase 2 — Explore the affected code

1. Use `Explore` agents to understand the current state of the code in affected areas.
2. Identify:
   - Files that will be modified or created.
   - Existing patterns that must be followed (consult `backend-patterns` skill).
   - Dependencies between components.
   - Known risks or pitfalls (consult MEMORY.md).
3. Present the user with a summary of findings and validate your understanding.

---

## Phase 3 — Write the proposal

Create the plan document at `docs/plans/<feature-name>.md` with this structure:

```markdown
# Feature name

## Context

What problem it solves. Why it is needed now.

## Decisions confirmed with user

| Topic | Decision |
|-------|----------|
| ... | ... |

## Design proposal

Conceptual design (not code). Components involved, data flow,
architecture decisions.

## Scope

### What is included
- ...

### What is NOT included
- ...

## Affected layers

| Layer | Impact |
|-------|--------|
| API (FastAPI) | ... |
| Application (services/ports) | ... |
| Domain (models) | ... |
| Infrastructure (OVH/ipify/SQLite) | ... |
| Tests | ... |
| Docker / CI | ... |

## Implementation order

Numbered list of high-level steps.

## Critical files

| File | Changes |
|------|---------|
| ... | ... |

## Risks and considerations

- ...

## Open design decisions

(If there are decisions yet to be made, list them here. They must be closed before creating tasks.)
```

Present the document to the user and ask for feedback.

---

## Phase 4 — Iterate until approval

- If the user has feedback, adjust the document.
- If there are open decisions, close them with `AskUserQuestion`.
- Once approved, tell the user: **"Plan saved. Next step: `/dev-2-tasks docs/plans/<feature-name>.md`"**

---

## Unbreakable rules

- **Do not implement anything**: no code, no tasks, no files beyond the plan document.
- **Ask before assuming**: if in doubt, use `AskUserQuestion`. Always.
- **Read the actual code** before proposing changes to existing areas.
- **The document must be self-contained**: someone reading it without prior context must understand the proposal.
- **All exploration commands via Docker** (dev-workflow skill).
