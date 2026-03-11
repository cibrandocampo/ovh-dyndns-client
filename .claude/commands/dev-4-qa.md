---
description: Forensic QA of a completed task — independent verification with evidence
argument-hint: <task-id, e.g.: T001>
---

# QA Review: $1

**Goal**: independently verify that the task meets its DoD. You produce real evidence or declare failure. No middle ground.
**Key behaviour**: you do not trust evidence from `/dev-3-run`. You re-execute everything from scratch. Anything broken — even if unrelated to the task — is a blocker. Never approve on top of a broken system.

---

## Step 1 — Read the task file

1. Locate the file `docs/tasks/$1*.md` and read it in full.
2. Extract:
   - **DoD**: the acceptance criteria.
   - **Evidence table**: commands, files, conditions.
   - **Dependencies**: are they completed?
3. Read the execution evidence from `/dev-3-run` (section `## Execution evidence`).
4. Read `CLAUDE.md` and `MEMORY.md` for context.

---

## Step 2 — Prepare environment and evidence

```bash
mkdir -p docs/tasks/evidence/$TASK_ID/qa
```

QA evidence goes separate from dev-3-run evidence to avoid contamination.

Make sure the dev environment is running:
```bash
docker compose -f dev/docker-compose.yaml ps
```

If the container is not running, start it before continuing:
```bash
docker compose -f dev/docker-compose.yaml up -d
```

---

## Step 3 — Progressive verification

**Do not trust dev-3-run evidence. Re-execute EVERYTHING.**

Verification follows a strict order from smallest to largest scope. If a phase fails,
the following phases are meaningless — skip directly to the verdict (Step 5).

Each command saves its evidence:
```bash
<command> 2>&1 | tee docs/tasks/evidence/$TASK_ID/qa/<file>.txt
```

### 3.1 — Lint & format

Run linters and formatters. **If they fail, fix before continuing.**

```bash
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff check . 2>&1 | tee docs/tasks/evidence/$TASK_ID/qa/ruff_check.txt
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff format --check . 2>&1 | tee docs/tasks/evidence/$TASK_ID/qa/ruff_format.txt
```

**If any fail:**
1. Fix: `ruff format .` / `ruff check --fix .`
2. Re-run checks and save clean evidence.
3. Note the correction in the QA report (not a blocker, but documented).

### 3.2 — Unit tests (targeted)

Run tests **only for the files modified by the task**.

1. Read the "Files to create/modify" section of the task file.
2. Identify the affected test files in `test/`.
3. Run only those:

```bash
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/<file>.py -v 2>&1 | tee docs/tasks/evidence/$TASK_ID/qa/unit_targeted.txt
```

If targeted unit tests fail → **RETURNED immediately**.
There is no point continuing with integration or E2E on code that fails its own tests.

### 3.2b — Coverage of new lines

**Run after 3.2 passes.** Check that every file modified by the task has adequate coverage.

```bash
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/ --cov=. --cov-report=term-missing 2>&1 | tee docs/tasks/evidence/$TASK_ID/qa/coverage.txt
```

Read the output. For **each file listed in "Files to create/modify"** of the task:
- Any file with uncovered lines that relate to the task's new code → **FAIL (blocker)**.
- Overall coverage must remain ≥70%.

**If coverage fails → RETURNED immediately.**

### 3.3 — Full test suite

Run the complete suite to detect regressions:

```bash
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/ -v 2>&1 | tee docs/tasks/evidence/$TASK_ID/qa/full_suite.txt
```

If there are failures here that were not in 3.2, the task introduced a regression → **RETURNED**.

### 3.4 — E2E tests (Playwright)

**Run if** the task modifies any API endpoint or user-visible behaviour.
**Skip if** the task is internal-only with no API changes (document why it was skipped).

```bash
docker run --rm --network host \
  -e E2E_USERNAME=admin \
  -e E2E_PASSWORD=admin123 \
  ovh-dyndns-e2e npx playwright test 2>&1 | tee docs/tasks/evidence/$TASK_ID/qa/e2e.txt
```

Only **new** failures or those related to the task count as blockers.

### 3.5 — Functional DoD checks

Go through EACH DoD item from the task file that **is not lint or tests** (those are
already covered in 3.1–3.4). Typical examples:

- Endpoint responds with expected status → `curl -sv ... 2>&1 | tee ...`
- Domain model has correct field/default → Read the file
- File created with expected content → Read tool
- DNS record updated via OVH API → inspect logs or curl response

For each functional check, execute the real command and save evidence:
```bash
<command> 2>&1 | tee docs/tasks/evidence/$TASK_ID/qa/dod_<name>.txt
```

**Don't invent checks**: only verify what the task's DoD explicitly requires.

### Evidence file verification

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

## Step 4 — Code review and scope

**Only if ALL Step 3 checks passed.** If there is any FAIL, skip directly to the verdict.

### 4.1 — Scope verification

Compare the task's objective with what was actually implemented:

1. Re-read the **"Objective"** section of the task file.
2. Go through each step of the task file and verify it was completed:
   - Was each file listed in "Files to create/modify" actually created/modified?
   - Is any deliverable described in the steps missing?
   - Was anything out of scope implemented that shouldn't be?
3. If a deliverable is missing or the objective is not met → blocker.

### 4.2 — Code review

Read the code modified/created by the task:

1. Read all files listed in "Files to create/modify" of the task file.
2. Verify:
   - Does it follow project conventions? (`backend-patterns` skill)
   - Are there security issues? (injection, exposed secrets, unprotected endpoints)
   - Are there uncovered edge cases?
   - Is the code clean and maintainable?
   - Do the tests cover the relevant cases for the task?
3. If you find issues: they are additional blockers (B1, B2...).

---

## Step 5 — Verdict

### Build verification table

| # | Phase | Deliverable | Evidence file | Condition | Result |
|---|-------|------------|---------------|-----------|--------|
| 1 | 3.1 | Lint (ruff check) | `qa/ruff_check.txt` | No errors | PASS/FAIL |
| 2 | 3.1 | Format (ruff format) | `qa/ruff_format.txt` | No diffs | PASS/FAIL |
| 3 | 3.2 | Unit tests (targeted) | `qa/unit_targeted.txt` | 0 failures | PASS/FAIL |
| 4 | 3.2b | Coverage | `qa/coverage.txt` | ≥70%, new lines covered | PASS/FAIL |
| 5 | 3.3 | Full test suite | `qa/full_suite.txt` | 0 failures | PASS/FAIL |
| 6 | 3.4 | E2E tests | `qa/e2e.txt` | No new failures | PASS/FAIL or N/A |
| 7 | 3.5 | Functional DoD checks | `qa/dod_*.txt` | Per DoD | PASS/FAIL |
| 8 | 4.1 | Scope completed | — | Objective met | PASS/FAIL |
| 9 | 4.2 | Code review | — | No issues | PASS/FAIL |

### If all PASS → APPROVED

Append to the task file:

```markdown
## Code Review — APPROVED

**Date**: YYYY-MM-DD

### QA verification

| # | Deliverable | Evidence | Result |
|---|------------|----------|--------|
| 1 | ... | `tasks/evidence/TXXX/qa/...` | PASS |

### Observations

(Positive notes, minor non-blocking suggestions if any)
```

### If any FAIL → RETURNED

Append to the task file:

```markdown
## Code Review — RETURNED

**Date**: YYYY-MM-DD

### QA verification

| # | Deliverable | Evidence | Result |
|---|------------|----------|--------|
| 1 | ... | `tasks/evidence/TXXX/qa/...` | FAIL |

### Blockers

- **B1**: Exact description of the problem. Affected file and line. What was expected vs what occurred.
- **B2**: ...

### Required action

Run `/dev-3-run $1` to fix the listed blockers.
```

---

## Final step — Update INDEX.md

1. Read `docs/tasks/INDEX.md`.
2. Update the **QA** column for the task:
   - APPROVED → `Approved`
   - RETURNED → `Returned (B1, B2...)`
3. If INDEX.md doesn't exist, skip without error.

---

## Absolute rules — etched in stone

- **If you didn't execute the command with Bash tool, you have no evidence.**
- **If the output is not in a physical file in `docs/tasks/evidence/`, you have no evidence.**
- **If you didn't read the file with Read tool, you have no evidence.**
- **"The code looks correct" is not evidence.**
- **"The previous task verified it" is not evidence.**
- **Never approve under time or attempt pressure.**
- **Missing file = command not executed = FAIL.**
- **Empty file = FAIL.**
