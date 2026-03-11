---
name: git-conventions
description: Git commit message conventions and branch naming standards for ovh-dyndns-client. Use when creating commits, branches, or preparing code for version control. Triggers on commit creation, branch creation, or when user asks about git workflow conventions.
---

# Git Conventions — ovh-dyndns-client

## Commit Message Format

```
<type>: <subject>

<bullet points explaining what changed and why>
```

### Rules

1. **Type**: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `style`
2. **Subject**: imperative mood, lowercase, no period at end
3. **Body**: bullet points grouped by area (api, domain, infrastructure, tests, docker, etc.)
4. **Co-Authored-By**: NEVER include Co-Authored-By lines
5. **Language**: always English, even if the conversation was in Spanish
6. **Author/Committer**: always use the git config from the current PC (never hardcode or use other identities). New commits automatically use `git config user.name` and `git config user.email`.

## Branch naming

```
feat/<slug>    # new feature
fix/<slug>     # bug fix
chore/<slug>   # maintenance, refactor, tooling
```

Examples: `feat/ipv6-support`, `fix/ovh-token-refresh`, `chore/docker-hardening`

## PR workflow

`main` is the primary branch. Always work on a branch and open a PR:

```bash
git checkout -b <type>/<slug>
git push -u origin <type>/<slug>
gh pr create --title "<concise title>" --body "..."
```

Never `push --force`. If there are conflicts, resolve with merge.

### Pre-commit hook

The project has a pre-commit hook (`scripts/pre-commit`) that runs:
- `ruff check .` — linting
- `ruff format --check .` — format verification

If the hook fails, **fix the issue and create a NEW commit** (never `--amend`).
To format before committing:
```bash
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff format .
```

### Example

```
feat: add IPv6 support for DNS record updates

- Add AAAA record type alongside A record in OVH adapter
- Extend domain model to hold optional ipv6 field
- Add ipify IPv6 endpoint to infrastructure config
- Cover new paths in unit tests
```
