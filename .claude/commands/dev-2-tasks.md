---
description: Create executable tasks from a feature plan
argument-hint: <path to plan or feature name>
---

# Create tasks: $1

**Goal**: split a plan into self-contained tasks, each executable with `/dev-3-run` in a single session.
**Behaviour**: you only divide and generate task files. No code, no implementation.

---

## Phase 1 — Locate and read the plan

1. If `$1` is a path, read it directly.
2. If it is a name, search `docs/plans/` for a matching file.
3. If there is no plan, inform the user: "No plan found. Run `/dev-1-plan` first to create one."
4. Read `CLAUDE.md`, `MEMORY.md`, and `docs/tasks/INDEX.md` (if it exists) for context and to avoid ID collisions.

---

## Phase 2 — Divide into tasks

### Criteria for each task

- **Self-contained**: executable without additional context beyond what the .md says.
- **One Claude session**: scope achievable in a single `/dev-3-run` execution.
- **Explicit dependencies**: if it depends on another task, it must be declared.
- **Verifiable**: each task has a DoD with real commands and an evidence table.

### Division process

1. Identify the affected layers (API, application, domain, infrastructure, tests).
2. Group changes by layer — each layer is usually 1 task.
3. Integration or e2e tests (if they cross multiple layers) are always the last task.
4. **Present the division to the user BEFORE creating files**:
   - Table with ID, title, dependencies, layer.
   - ASCII dependency graph.
   - Ask if anything is missing, redundant, or incorrectly ordered.

**Adjust based on user feedback before creating any files.**

---

## Phase 3 — Generate task files

### Assign IDs

- Format: `TXXX` (e.g.: T001, T002... or T018, T019 if there are prior tasks).
- Read `docs/tasks/INDEX.md` to find the last used ID. If it doesn't exist, start at T001.
- Filename: `docs/tasks/TXXX_descriptive-name.md`

### Required structure for each task

Each file must follow EXACTLY this structure:

```markdown
# TXXX — Descriptive title

## Context

Why this task exists. What problem it solves within the feature.
Reference to the plan document if one exists.

**Dependencies**: TXXX (if applicable) or "None".

## Objective

Brief paragraph: what this task must achieve when completed.

## Step 1 — Step title

Concrete instructions. Example code if it aids clarity.
Each step is an identifiable unit of work.

## Step 2 — ...

(as many steps as needed)

## DoD — Definition of Done

Numbered list. Each item verifiable with a real command.
Never vague items like "works correctly" — always concrete.

1. Tests pass (`docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/ -v`)
2. ...

## Evidence to produce

| # | Description | Command | File | PASS condition |
|---|-------------|---------|------|----------------|
| 1 | Unit tests | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/ -v 2>&1` | `unit_tests.txt` | All tests pass, 0 failures |
| 2 | ... | ... | ... | ... |

## Files to create/modify

| File | Action |
|------|--------|
| `src/api/routers/hosts.py` | MODIFY |
| `src/domain/host.py` | CREATE |
```

### Content rules

- **No ambiguities**: if a step can be interpreted two ways, clarify it.
- **Example code**: only to illustrate the pattern, not as final implementation.
- **Docker commands**: always with `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev`.
- **No TODOs or placeholders**: every section complete.

---

## Phase 4 — Create/update INDEX.md

Create or update `docs/tasks/INDEX.md` with the following structure:

```markdown
# Task index — ovh-dyndns-client

## Series TXXX — Feature name

Plan: [docs/plans/feature-name.md](../docs/plans/feature-name.md)

| ID | Title | Dependencies | Status | QA |
|----|-------|-------------|--------|----|
| T001 | Description | — | Pending | — |
| T002 | Description | T001 | Pending | — |
| T003 | Description | T001 | Pending | — |

### Execution order

T001 ──→ T002 ──→ T004
  └────→ T003 ─┘
```

If INDEX.md already exists with previous series, add the new series without deleting existing ones.

> `INDEX.md` is only used by the `dev-X` path. `/fix` and `/audit` do not produce task files and do not touch INDEX.md.

---

## Final validation

Present the user with the complete summary:

- N tasks generated with their dependencies.
- INDEX.md updated.
- Next step: `/dev-3-run TXXX` to execute the first task.

Ask if they want to adjust anything. Iterate until approval.

---

## Unbreakable rules

- **Ask before assuming**: if in doubt, use `AskUserQuestion`.
- **Do not write files until you have approval** of the division (Phase 2).
- **Each task must be executable with `/dev-3-run TXXX`** without additional context.
- **Be critical of your own division**: is any task too large? Split it. Is any trivial? Merge.
- **Don't invent work**: if the plan says "no schema changes", don't add a migration task.
- **Read the actual code** before deciding which files are modified in each task.
- **The dependency graph must be correct**: if T003 depends on T001 but not T002, don't chain them unnecessarily.
