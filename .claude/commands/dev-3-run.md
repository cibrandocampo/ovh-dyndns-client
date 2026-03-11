---
description: Execute a task from the backlog
argument-hint: <task-id, e.g.: T001, T005_hosts>
---

# Execute task: $1

**Goal**: implement a backlog task and leave it ready for QA. Getting it right the first time minimises review cycles.

## Total ownership

This is a one-person team. **There is no such thing as a "pre-existing error".** If you encounter a system error during execution — even if unrelated to your code — it is your responsibility to fix it before continuing.

- If a DoD verification uncovers an unrelated failure (broken test, crashed service): **stop, diagnose, fix, then continue.**
- Never label an error as "pre-existing" to avoid responsibility.
- Evidence built on a broken system is invalid.

---

## Step 0 — Locate the task

Search in `docs/tasks/` for a file matching `$1`. It can be:
- Exact ID: `T001` → search `docs/tasks/T001*.md`
- Partial name: `T001_hosts` → search `docs/tasks/T001_hosts*.md`

If no match is found, list available files in `docs/tasks/` and ask the user to choose.

---

## Step 1 — Deep reading and context

1. Read the task file **in full**, including sections appended at the end.
2. **If there is a `## Code Review — RETURNED`**: this is a re-execution. Blockers (B1, B2...) are absolute priority. Read the actual code of each affected file and fix ALL of them before continuing with the rest of the DoD.
3. Read `CLAUDE.md` and `MEMORY.md` for project context.
4. Verify dependencies: if the task depends on another, confirm it was completed (check MEMORY.md or INDEX.md).
5. **Read the related existing code**: before writing a single line, read the files you will modify. Never write code without having read the actual context.

If any dependency is unresolved, inform the user and stop.

---

## Step 2 — Execution plan

1. Analyze each DoD item — these are your non-negotiable acceptance criteria.
2. Create a single TaskCreate for this execution. Use TaskUpdate to report progress as steps complete.
3. Review MEMORY.md for known pitfalls in this area.
4. If there are non-trivial design decisions, explain them to the user before proceeding.

---

## Step 3 — Execution

For each item in the task list:

1. Mark as `in_progress`.
2. **Before writing**: read the affected files. Understand existing patterns. Follow conventions from the `backend-patterns` skill.
3. Implement the complete deliverable. Strict rules:
   - **NO TODOs**: all code must be complete and functional.
   - **NO fake mocks**: if a test is required, it must execute and pass.
   - **NO placeholders**: every line must have real purpose.
   - **Clean code**: follow project conventions.
4. **Self-review**: re-read the code you wrote. Are there typos, missing imports, inconsistencies? Fix them.
5. Mark as `completed` only when the deliverable is finished and reviewed.

**All commands via Docker** — use `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev`.

---

## Step 4 — Verify DoD

Go through EACH DoD item and verify by executing real commands.

**Absolute rule: never consider something verified without executing a command that returns real output.**

### Save evidence to files

```bash
mkdir -p docs/tasks/evidence/$TASK_ID
```

For each DoD verification:
```bash
<command> 2>&1 | tee docs/tasks/evidence/$TASK_ID/<file>.txt
```

Then, read each file with Read tool and verify the condition.

### Format by deliverable type

| Type | Command | Verification |
|------|---------|-------------|
| Unit tests | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/ -v 2>&1` | All pass, 0 failures |
| Tests with coverage | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/ --cov=. --cov-report=term-missing 2>&1` | ≥70% coverage |
| Lint | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff check . 2>&1` | No errors |
| Format | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff format --check . 2>&1` | No diffs |
| HTTP endpoints | `curl -sv "http://localhost:8000/api/..." 2>&1` | Expected status + body |
| Created files | Read tool | Exists and correct content |

### Self-review before documenting

- Is each cited command the one I actually executed?
- Do the tests cover functionality from THIS task?
- Is there any DoD item I only verified by "the code looks correct"? → Execute the real command.

---

## Step 5 — Document evidence

Append to the task file:

```markdown
## Execution evidence

**Date**: YYYY-MM-DD
**Modified files**:
- `path/to/file.py` — description of change

### Verification table

| # | Deliverable | Evidence file | Result |
|---|------------|---------------|--------|
| 1 | Unit tests pass | `docs/tasks/evidence/TXXX/unit_tests.txt` | PASS |
| 2 | ... | ... | ... |

### Design decisions

- (if there were relevant decisions, document them here)
```

---

## Step 6 — Update state

1. **MEMORY.md**: if you discovered new patterns or pitfalls, update. Don't add redundant info.
2. **docs/tasks/INDEX.md**: mark the task as "Completed" in the Status column.

---

## Unbreakable rules

- Never mark a task as completed if any DoD item is not met.
- Never write evidence without a real command executed and saved to file.
- **Read before writing**: never modify code you haven't read.
- **Review after writing**: always re-read the produced code.
- **Do NOT commit**: that is `/push`'s responsibility.
- **Do NOT push**: that is `/push`'s responsibility.
- If you get blocked, ask the user instead of simplifying.
- Follow existing patterns; consult MEMORY.md and the project skills.
- Documentation language: English. Code language: English.
