---
description: Forensic QA of a completed task — independent verification with evidence
argument-hint: <task-id, e.g.: T001>
---

# QA Review: $1

**Goal**: independently verify that the task meets its DoD. You produce real evidence or declare failure. No middle ground.
**Key behaviour**: you do not trust evidence from `/dev-3-run`. You re-execute everything from scratch. Anything broken — even if unrelated to the task — is a blocker. Never approve on top of a broken system.

---

## Step 1 — Read the Task File

1. Locate the file `docs/tasks/$1*.md` and read it in full.
2. Extract:
   - **DoD**: the acceptance criteria.
   - **Evidence table**: commands, files, conditions.
   - **Dependencies**: are they completed?
3. Read the execution evidence from `/dev-3-run` (section `## Execution Evidence`).
4. Read `CLAUDE.md` and `MEMORY.md` for context.

---

## Step 2 — Prepare Evidence Folder

```bash
mkdir -p docs/tasks/evidence/$TASK_ID/qa
```

QA evidence goes separate from dev-3-run evidence to avoid contamination.

---

## Step 3 — Progressive Verification

**Do not trust dev-3-run evidence. Re-execute EVERYTHING.**

Verification follows a strict order from smallest to largest scope. If a phase fails, the following phases are meaningless — skip directly to the verdict (Step 5).

Each command saves its evidence:
```bash
<command> 2>&1 | tee docs/tasks/evidence/$TASK_ID/qa/<file>.txt
```

See `dev-workflow` skill for the project's specific lint, test, build, and E2E commands.

### 3.1 — Lint & Format

Run linters and formatters. **If they fail, fix before continuing.** Save output to `qa/lint_backend.txt`, `qa/lint_frontend.txt`, etc.

If any fail: fix, re-run, save clean evidence, note the correction in the QA report.

### 3.2 — Unit Tests (Targeted)

Run tests **only for the files/apps modified by the task**.

1. Read the "Files to Create/Modify" section of the task file.
2. Run only the tests covering those files. Save output to `qa/unit_<area>.txt`.

If targeted unit tests fail → **RETURNED immediately.**

### 3.2b — Coverage of New Lines

**Run after 3.2 passes.** For each file modified by the task, check coverage on new lines. Save output to `qa/coverage_<area>.txt`.

- **Target: 100%** on new lines — this is the goal and what codecov enforces.
- **Hard minimum: 95%** — below this, RETURNED immediately.
- Between 95–99%: document each uncovered line with an explicit justification in the QA report. Accept only if the justification is sound (e.g. a defensive branch that cannot be triggered without mocking internals).

> Lines that are structurally unreachable should be eliminated or refactored — not left uncovered.

If coverage is below 95% → **RETURNED immediately.**

### 3.3 — Integration Tests (Full Suites)

Run the full test suites to detect regressions in code not directly modified. Save output to `qa/tests_full.txt`.

If there are failures here that were not in 3.2, the task introduced a regression → **RETURNED.**

### 3.4 — E2E Tests

**Run if** the task modifies UI or introduces a user-visible flow.
**Skip if** the task is backend-only with no UI changes (document why it was skipped).

Save output to `qa/e2e.txt`. Only **new** failures or those related to the task count as blockers.

### 3.5 — Functional DoD Checks

Go through EACH DoD item from the task file that **is not lint or tests** (those are already covered in 3.1–3.4). For each functional check, execute the real command and save evidence to `qa/dod_<name>.txt`.

**Don't invent checks**: only verify what the task's DoD explicitly requires.

### Evidence File Verification

For EACH file generated in the previous phases:

1. `Read("docs/tasks/evidence/$TASK_ID/qa/<file>.txt")` — full read.
2. Apply the expected condition.
3. Record: PASS or FAIL with the exact reason.

**Absolute rules:**
- File **does not exist** → FAIL automatic (the command was not executed).
- File **is empty** → FAIL automatic.
- Condition not met → FAIL. Copy the fragment from the file that proves it.
- Never evaluate "from memory" — always read the file with Read tool.

---

## Step 4 — Code Review and Scope

**Only if ALL Step 3 checks passed.** If there is any FAIL, skip directly to the verdict.

### 4.1 — Scope Verification

1. Re-read the **"Objective"** section of the task file.
2. Verify each step was completed: files listed in "Files to Create/Modify" exist with the right changes, no out-of-scope work was added.

### 4.2 — Code Review

Read all files listed in "Files to Create/Modify":
- Does it follow project conventions? (consult `.claude/skills/`)
- Are there security issues? (injection, XSS, exposed data)
- Are there uncovered edge cases?
- Do the tests cover the relevant cases for the task?

---

## Step 5 — Verdict

### Build Verification Table

| # | Phase | Deliverable | Evidence file | Condition | Result |
|---|-------|------------|---------------|-----------|--------|
| 1 | 3.1 | Lint | `qa/lint_*.txt` | No errors | PASS/FAIL |
| 2 | 3.2 | Unit tests (targeted) | `qa/unit_*.txt` | 0 failures | PASS/FAIL |
| 3 | 3.2b | Coverage | `qa/coverage_*.txt` | 0 uncovered lines in modified files | PASS/FAIL |
| 4 | 3.3 | Full test suite | `qa/tests_full.txt` | 0 failures | PASS/FAIL |
| 5 | 3.4 | E2E tests | `qa/e2e.txt` | No new failures | PASS/FAIL or N/A |
| 6 | 3.5 | Functional DoD | `qa/dod_*.txt` | Per DoD | PASS/FAIL |
| 7 | 4.1 | Scope completed | — | Objective met | PASS/FAIL |
| 8 | 4.2 | Code review | — | No issues | PASS/FAIL |

### If All PASS → APPROVED

Append to the task file:

```markdown
## Code Review — APPROVED

**Date**: YYYY-MM-DD

### QA Verification

| # | Deliverable | Evidence | Result |
|---|------------|----------|--------|
| 1 | ... | `tasks/evidence/TXXX/qa/...` | PASS |

### Observations

(Positive notes, minor non-blocking suggestions if any)
```

### If Any FAIL → RETURNED

Append to the task file:

```markdown
## Code Review — RETURNED

**Date**: YYYY-MM-DD

### QA Verification

| # | Deliverable | Evidence | Result |
|---|------------|----------|--------|
| 1 | ... | `tasks/evidence/TXXX/qa/...` | FAIL |

### Blockers

- **B1**: Exact description of the problem. Affected file and line. What was expected vs what occurred.
- **B2**: ...

### Required Action

Run `/dev-3-run $1` to fix the listed blockers.
```

---

## Final Step — Update INDEX.md and Suggest Next Action

1. Read `docs/tasks/INDEX.md`.
2. Update the **QA** column for the task: APPROVED → `Approved`, RETURNED → `Returned (B1, B2...)`.
3. If INDEX.md doesn't exist, skip without error.

### If APPROVED — check whether the feature is complete

Read the full series in INDEX.md:
- **If there are pending tasks**: inform the user and suggest the next one:
  > "Task TXXX approved. Next: `/dev-3-run TYYY`"
- **If all tasks in the series are approved**: the feature is complete. Suggest closing the cycle:
  > "All tasks approved. Ready to commit and open a PR: `/push`"

> By default, the commit happens once — when the full feature is done, not after each task.
> If the user wants to commit after a specific task, they can run `/push` at any point.

---

## Absolute Rules — Etched in Stone

- **If you didn't execute the command with Bash tool, you have no evidence.**
- **If the output is not in a physical file in `docs/tasks/evidence/`, you have no evidence.**
- **If you didn't read the file with Read tool, you have no evidence.**
- **"The code looks correct" is not evidence.**
- **"The previous task verified it" is not evidence.**
- **Never approve under time or attempt pressure.**
- **Missing file = command not executed = FAIL.**
- **Empty file = FAIL.**
