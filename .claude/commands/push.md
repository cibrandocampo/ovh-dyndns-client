---
description: Update documentation, commit, create PR, and verify CI pipeline
argument-hint: <change description or task-id (optional)>
---

# Push: $1

**Goal**: close the work cycle — documentation updated, clean commit, PR created, pipeline green.
**Behaviour**: you are the last gate before code reaches review. Never commit with broken tests. Never ignore CI failures.

---

## Step 1 — Review Current State

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

## Step 2 — Update Documentation

Skip this step entirely if the changes came from `/fix` and touched no structure, conventions, or configuration.

Otherwise, review whether the changes require documentation updates:

### Documentation Checklist

- [ ] **`docs/configuration.md`**: are there new environment variables? Did any existing one change?
- [ ] **`README.md`**: do the changes affect installation or usage instructions?
- [ ] **`CLAUDE.md`**: are there new patterns or conventions Claude should know?
- [ ] **Skills (`.claude/skills/`)**: did any convention documented in a skill change?
- [ ] **`docs/ARCHITECTURE.md`**: did the system architecture change?

For each applicable item: read the current file, update with the new information, don't add unnecessary documentation.

---

## Step 3 — Pre-Commit Validation

**Skip this step if `$1` has `## Code Review — APPROVED`** — QA already ran the full suite.

Otherwise, run the pre-commit sequence defined in the `git-conventions` skill. Do not proceed if any step fails.

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

### Create Branch (if needed)

If you are on `main`, create a descriptive branch:
```bash
git checkout -b <type>/<descriptive-name>
```

### Push

```bash
git push -u origin <branch>
```

**Never `push --force`.**

### Create PR

Invoke the `pr-create` skill — it will analyse the branch, build the PR body, and open the PR.

---

## Step 6 — Verify CI

Monitor the pipeline after the PR is created:

```bash
gh pr checks <pr-number> --watch
```

### If the Pipeline Fails

1. Identify which job failed: `gh run view <run-id> --log-failed`
2. Diagnose the error.
3. Fix locally and verify it passes.
4. Create a **new commit** (not amend) and push.
5. Repeat until pipeline is green.

### When the Pipeline Passes

Inform the user with:
- PR URL
- Pipeline status (green)
- Summary of what the PR includes

---

## Unbreakable Rules

- **`git-conventions` skill**: apply it for the pre-commit sequence, commit format, and pre-commit hook handling.
- **Never `push --force`**: if there are conflicts, resolve with merge.
- **Green pipeline**: do not consider it done until CI passes.
- **If CI fails, fix it**: do not ignore it or ask the user to handle it manually.
- **Commit and PR language**: always English.
