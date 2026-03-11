---
description: Update documentation, commit with pre-commit, create PR, and verify CI pipeline
argument-hint: <change description or task-id (optional)>
---

# Push: $1

**Goal**: close the work cycle — documentation updated, clean commit, PR created, pipeline green.
**Behaviour**: you are the last gate before code reaches review. Never commit with broken tests. Never ignore CI failures.

---

## Step 1 — Review current state

1. Run `git status` to see modified, added, and untracked files.
2. Run `git diff --stat` to see a summary of changes.
3. If `$1` references a task-id, read `docs/tasks/$1*.md` in full:
   - Extract commit context (objective, modified files, design decisions).
   - **Check for `## Code Review — APPROVED`**. If it is missing, warn the user:
     > "This task has not been QA-approved. Run `/dev-4-qa $1` first, or confirm you want to push anyway."
   - Do not proceed until the user confirms.
4. If there is no `$1`, review modified files to understand what changed.

If there are no changes, inform the user and stop.

---

## Step 2 — Update documentation

Review whether the changes require documentation updates:

### Documentation checklist

- [ ] **`README.md`**: do the changes affect installation or usage instructions?
- [ ] **`CLAUDE.md`**: are there new patterns or conventions Claude should know?
- [ ] **Skills (`.claude/skills/`)**: did any convention documented in a skill change?
- [ ] **`docs/`**: did the architecture, configuration, or API contract change?

For each applicable item:
1. Read the current file.
2. Update with the new information.
3. Don't add unnecessary documentation — only what changed.

Ask the user with `AskUserQuestion` if there is anything additional to document.

---

## Step 3 — Verify tests locally

**Skip this step if `$1` has `## Code Review — APPROVED`** — QA already ran the full suite.

Otherwise, make sure the dev environment is running:
```bash
docker compose -f dev/docker-compose.yaml ps
```

Run lint and tests:
```bash
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff check .
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff format --check .
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/ -v
```

If any fail: **stop, fix, and re-verify.** Do not commit with broken tests.

---

## Step 4 — Commit

**Strictly apply the `git-conventions` skill** for format, rules, and pre-commit hook handling.

```bash
git add <specific files>
git commit -m "$(cat <<'EOF'
<type>: <subject>

- bullet points
EOF
)"
```

If the pre-commit hook fails: fix, `git add`, new commit (never `--amend`).

---

## Step 5 — Pull Request

### Create branch (if needed)

If you are on `main`, create a descriptive branch:
```bash
git checkout -b <type>/<descriptive-name>
```

Examples: `feat/ipv6-support`, `fix/ovh-token-refresh`, `chore/docker-hardening`

### Push

```bash
git push -u origin <branch>
```

**Never `push --force`.**

### Create PR

```bash
gh pr create --title "<concise title>" --body "$(cat <<'EOF'
## Summary

- Bullet 1
- Bullet 2

## Test plan

- [ ] Unit tests pass
- [ ] Lint/format clean
- [ ] (other specific checks)
EOF
)"
```

- Title: <70 characters, in English
- Body: clear summary + test plan with checklist

---

## Step 6 — Verify CI

The GitHub Actions pipeline runs:
- `lint-and-test`: ruff check + ruff format --check + pytest with coverage
- `docker-build`: builds and pushes Docker image (on main/tag only)

### Monitor

```bash
gh pr checks <pr-number> --watch
```

Or to see the status of a specific run:
```bash
gh run list --limit 1
gh run view <run-id>
```

### If the pipeline fails

1. Identify which job failed:
   ```bash
   gh run view <run-id> --log-failed
   ```
2. Diagnose the error in the output.
3. Fix locally.
4. Verify it passes locally (tests + lint).
5. Create a **new commit** (not amend) and push.
6. Repeat until pipeline is green.

### When the pipeline passes

Inform the user with:
- PR URL
- Pipeline status (green)
- Summary of what the PR includes

---

## Unbreakable rules

- **Local tests BEFORE commit**: never commit without verifying.
- **Apply `git-conventions` skill**: format, commit rules, and pre-commit hook handling.
- **Never `push --force`**: if there are conflicts, resolve with merge.
- **Green pipeline**: do not consider it done until CI passes.
- **If CI fails, fix it**: do not ignore it or ask the user to handle it manually.
- **Commit and PR language**: always English.
