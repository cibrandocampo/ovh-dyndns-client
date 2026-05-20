---
description: Analyze branch changes and create a GitHub PR with a structured, relevance-ordered body
argument-hint: <base-branch (optional)>
---

# Create PR

**Goal**: understand what changed in this branch, then open a GitHub PR with a well-structured body.
**Base branch**: use `$1` if provided. Otherwise auto-detect: use `develop` if it exists, then `main`, then `master`.

```bash
# Detect base branch (skip if $1 was provided)
git branch --list develop main master
```

---

## Step 1 — Understand the Branch

Run these commands to gather full context (replace `<base>` with the detected base branch):

```bash
git branch --show-current
git log <base>..HEAD --oneline
git diff <base>...HEAD --stat
git diff <base>...HEAD
```

Read any task file referenced by the commits (`docs/tasks/*.md`) if it exists — it contains objective, design decisions, and test results from QA.

---

## Step 2 — Analyse the Changes

From the diff and commit log, extract:

1. **What changed** — group by area (backend model, API endpoint, frontend component, infra, config, etc.).
2. **Impact on the project** — rank each change by how much it affects live functionality:
   - High: changes to data models, API contracts, authentication, background jobs, core business logic.
   - Medium: new UI behaviour, new endpoints, config changes that affect runtime.
   - Low: refactors with no behaviour change, test additions, style fixes, documentation.
3. **Resolved issues** — check commit messages and task files for "closes #N", "fixes #N", or any explicit issue references.
4. **Critical design decisions** — anything non-obvious that was deliberately chosen over an alternative.
5. **Test evidence** — what tests were actually run (from QA task or local verification), and what a reviewer should run to validate.

---

## Step 3 — Write the PR Body

Use this exact structure. Omit sections that don't apply (Issues, Notes).

```
## Summary

- <change — most impactful first>
- <change>
- <change — least impactful last>

## Issues

Closes #<n>

## Notes

> **Note**: <critical design decision and brief rationale>

## Test plan

- [x] <test that was already executed>
- [ ] <test a reviewer must run to validate>
```

### Rules for Each Section

**Summary**
- Bullet points ordered from highest to lowest functional impact.
- Each bullet describes *what* changed and *why*, not just the file name.
- Be concrete: "Add `consumed_lots` JSONField to persist per-lot consumption" — not "backend changes".
- Maximum ~6 bullets; group minor items if needed.

**Issues** _(omit if no issue was resolved)_
- One `Closes #n` line per resolved issue.

**Notes** _(omit if no critical design decision was made)_
- One blockquote per decision.
- Format: `> **Note**: <decision>. <rationale in one sentence>.`

**Test plan**
- `[x]` for tests already confirmed passing (local or CI).
- `[ ]` for tests a reviewer must run before merging.
- Be specific: name the test file, the button to click, the API call to make.

---

## Step 4 — Create Branch and PR

### Branch (if still on base branch)

```bash
git checkout -b <type>/<descriptive-slug>
git push -u origin <type>/<descriptive-slug>
```

### PR Title

- Under 70 characters.
- Imperative mood, lowercase type prefix: `feat:`, `fix:`, `chore:`.
- English only.

### Create

```bash
gh pr create --title "<title>" --body "$(cat <<'EOF'
<body>
EOF
)"
```

---

## Unbreakable Rules

- **English only** — title, body, bullet points, notes, everything.
- **No authorship attribution** — do not mention any tool, assistant, or generator anywhere in the PR.
- **Relevance order** — Summary bullets must go from most to least impactful; never alphabetical or file-order.
- **Evidence-based test plan** — only mark `[x]` if you have confirmed the test passed; never pre-check unrun tests.
- **Omit empty sections** — if there are no resolved issues, drop the Issues section entirely. Same for Notes.
