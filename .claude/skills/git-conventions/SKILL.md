---
name: git-conventions
description: Git commit message conventions and branch naming standards. Use when creating commits, branches, or preparing code for version control. Triggers on commit creation, branch creation, or when user asks about git workflow conventions.
---

# Git Conventions — ovh-dyndns-client

## Commit message format

```
<type>: <subject>

<bullet points explaining what changed and why>
```

### Rules

1. **Type**: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `style`
2. **Subject**: imperative mood, lowercase, no period at the end
3. **Body**: bullet points grouped by area when multiple changes are involved
4. **Co-Authored-By**: NEVER include Co-Authored-By lines
5. **Language**: always English, even if the conversation is in Spanish
6. **Author/Committer**: always use the git config from the current machine (never hardcode identities)

### Example

```
feat: add force-update button per host in status page

- Add POST /hosts/{id}/update endpoint to trigger immediate DNS update
- Show per-host force update button in status table
- Display inline success/error message instead of browser alert
- Update last_check timestamp on every check regardless of IP change
```

### Pre-commit hook

The project has a hook at `scripts/pre-commit` that runs:
- `ruff check .` — linting
- `ruff format --check .` — format verification

If the hook fails, **fix the issue and create a new commit** (never `--amend`).

To format before committing:
```bash
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff format .
```
