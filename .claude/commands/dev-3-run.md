---
description: Execute a task from the backlog
argument-hint: <task-id, e.g.: T001, T005_auth>
---

# Execute Task: $1

**Goal**: implement a backlog task and leave it ready for QA. Getting it right the first time minimises review cycles.

## Total Ownership

This is a one-person team. **There is no such thing as a "pre-existing error".** If you encounter a system error during execution — even if unrelated to your code — it is your responsibility to fix it before continuing.

- If a DoD verification uncovers an unrelated failure: **stop, diagnose, fix, then continue.**
- Never label an error as "pre-existing" to avoid responsibility.
- Evidence built on a broken system is invalid.

---

## Step 0 — Locate the Task and Prepare the Branch

### Locate the task

Search in `docs/tasks/` for a file matching `$1`. It can be:
- Exact ID: `T001` → search `docs/tasks/T001*.md`
- Partial name: `T001_auth` → search `docs/tasks/T001_auth*.md`

If no match is found, list available files in `docs/tasks/` and ask the user to choose.

### Create the feature branch (first task only)

Check `docs/tasks/INDEX.md` to determine if this is the **first task of the series** (no prior tasks with status "Completed" in the same series).

If it is the first task:

1. Read the plan document linked in INDEX.md and extract the `## Branch` value.
2. Check if the branch already exists:
   ```bash
   git branch --list <branch-name>
   ```
3. If it does not exist, create it from the right base:
   ```bash
   # Use develop if it exists, otherwise main/master
   git checkout develop 2>/dev/null || git checkout main 2>/dev/null || git checkout master
   git pull
   git checkout -b <branch-name>
   ```
4. If it already exists, check it out:
   ```bash
   git checkout <branch-name>
   ```

If this is not the first task, verify you are already on the correct branch before continuing.

---

## Step 1 — Deep Reading and Context

1. Read the task file **in full**, including sections appended at the end.
2. **If there is a `## Code Review — RETURNED`**: this is a re-execution. Blockers (B1, B2...) are absolute priority. Read the actual code of each affected file and fix ALL of them before continuing.
3. Read `CLAUDE.md` and `MEMORY.md` for project context.
4. Verify dependencies: if the task depends on another, confirm it was completed (check MEMORY.md or INDEX.md).
5. **Read the related existing code**: before writing a single line, read the files you will modify.

If any dependency is unresolved, inform the user and stop.

---

## Step 2 — Execution Plan

1. Analyze each DoD item — these are your non-negotiable acceptance criteria.
2. **Consult the `architecture` skill** — run through the validation checklist before writing any code. If you spot a red flag, surface it to the user before proceeding.
3. Create a single TaskCreate for this execution. Use TaskUpdate to report progress as steps complete.
4. Review MEMORY.md for known pitfalls in this area.
5. If there are non-trivial design decisions, explain them to the user before proceeding.

---

## Step 3 — Execution

For each item in the task list:

1. Mark as `in_progress`.
2. **Before writing**: read the affected files. Understand existing patterns. Follow conventions from the relevant project skills (`.claude/skills/`).
3. Implement the complete deliverable. Strict rules:
   - **NO TODOs**: all code must be complete and functional.
   - **NO fake mocks**: if a test is required, it must execute and pass.
   - **NO placeholders**: every line must have real purpose.
   - **Clean code**: follow project conventions.
4. **Self-review**: re-read the code you wrote. Are there typos, missing imports, inconsistencies? Fix them.
5. Mark as `completed` only when the deliverable is finished and reviewed.

### If the task grows mid-execution

If during implementation you discover that the scope is significantly larger than the task described — unexpected dependencies, missing foundations, design decisions that require user input — **stop immediately**. Do not push forward with a half-baked solution.

Inform the user:
- What you found and why it changes the scope.
- What has been done so far (if anything).
- Suggest: **"This is better handled with `/dev-1-plan` to redesign the approach before continuing."**

Leave the code in a clean state (no broken imports, no half-written functions) before stopping.

---

## Step 4 — Verify DoD

Go through EACH DoD item and verify by executing real commands (see `dev-workflow` skill for project-specific commands).

**Absolute rule: never consider something verified without executing a command that returns real output.**

### Save Evidence to Files

```bash
mkdir -p docs/tasks/evidence/$TASK_ID
```

For each DoD verification:
```bash
<command> 2>&1 | tee docs/tasks/evidence/$TASK_ID/<file>.txt
```

Then, read each file with Read tool and verify the condition.

### Self-Review Before Documenting

- Is each cited command the one I actually executed?
- Do the tests cover functionality from THIS task?
- Is there any DoD item I only verified by "the code looks correct"? → Execute the real command.

---

## Step 5 — Document Evidence

Append to the task file:

```markdown
## Execution Evidence

**Date**: YYYY-MM-DD
**Modified files**:
- `path/to/file.py` — description of change

### Verification Table

| # | Deliverable | Evidence file | Result |
|---|------------|---------------|--------|
| 1 | Tests pass | `docs/tasks/evidence/TXXX/tests.txt` | PASS |
| 2 | ... | ... | ... |

### Design Decisions

- (if there were relevant decisions, document them here)
```

---

## Step 6 — Update State

1. **MEMORY.md**: if you discovered new patterns or pitfalls, update. Don't add redundant info.
2. **docs/tasks/INDEX.md**: mark the task as "Completed" in the Status column.

---

## Unbreakable Rules

- Never mark a task as completed if any DoD item is not met.
- Never write evidence without a real command executed and saved to file.
- **Read before writing**: never modify code you haven't read.
- **Review after writing**: always re-read the produced code.
- **Do NOT commit**: that is `/push`'s responsibility.
- **Do NOT push**: that is `/push`'s responsibility.
- If you get blocked, ask the user instead of simplifying.
- Follow existing patterns; consult MEMORY.md and the project skills.
