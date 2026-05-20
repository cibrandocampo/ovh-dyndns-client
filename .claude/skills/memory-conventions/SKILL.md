---
name: memory-conventions
description: How to use MEMORY.md — what to record, how to structure it, and when to update it. Use whenever writing to or reading from MEMORY.md.
---

# Memory Conventions

## Two Memory Systems — Use the Right One

Claude Code has two distinct memory systems. Do not confuse them.

| | `MEMORY.md` (project) | Auto-memory (harness) |
|---|---|---|
| **Lives in** | Project root, committed to the repo | `~/.claude/projects/.../memory/` |
| **Scope** | Project knowledge | User preferences |
| **Who sees it** | Any developer (or Claude) working on this repo | Only the current user |
| **Contains** | Gotchas, architecture decisions, env quirks, recurring patterns | User feedback, workflow preferences, personal context |

**Rule**: if the knowledge is about the project (technical, architectural, environmental), it goes in `MEMORY.md`. If it is about how the user works or what they prefer, it goes in the harness auto-memory.

---

`MEMORY.md` is a living document that captures project knowledge that is **not derivable from reading the code**. It bridges sessions and developers — what is learned working on this project should not be re-learned next time.

## What to Record in MEMORY.md

### Record these:
- **Gotchas and traps**: things that look one way but behave another. "The X service must be restarted after changing Y, or the change is not picked up."
- **Non-obvious decisions**: architectural or product choices that were made deliberately and would confuse a future reader. "We use polling instead of websockets because Z constraint."
- **Environment quirks**: infra behaviour that deviates from the expected. "In dev, the cache is disabled — behaviour differs from prod."
- **Project context**: current phase, priorities, constraints that affect how work should be scoped.
- **Recurring patterns**: "When adding a new entity, always register it in X, Y, and Z."

### Do NOT record these:
- Code that already exists in the repo — read the source.
- Git history — use `git log`.
- Things already documented in `CLAUDE.md` or skill files — don't duplicate.
- Temporary task state or in-progress notes — those belong in task files.
- Anything obvious from reading the code with normal attention.
- User preferences or workflow feedback — those belong in the harness auto-memory.

## Structure

Use sections with clear headings. Suggested sections:

```markdown
# MEMORY — <Project Name>

## Architecture decisions

- **Decision**: <what was decided>. **Why**: <the constraint or reasoning>. **Date**: YYYY-MM.

## Gotchas

- **<Area>**: <what the trap is and how to avoid it>.

## Environment

- **<Topic>**: <quirk and explanation>.

## Recurring patterns

- **<Pattern name>**: <when to use it and how>.

## Current context

- **<Topic>**: <status, priority, or constraint that affects ongoing work>.
```

## How to Write an Entry

**Good entry:**
> **Gotchas / Auth**: The `refresh_token` endpoint does not return a new access token if the old one is still valid (< 5 min to expiry). Tests that expect a new token immediately after login will fail intermittently depending on timing. Always force expiry in test setup.

**Bad entry:**
> Added refresh token logic in auth.py.

The good entry captures *why* something is surprising and *how to handle it*. The bad entry just restates what the code says.

## When to Update

- **After a gotcha bites you**: write it down immediately, before moving on.
- **After a significant architecture decision**: record what was decided and why.
- **After discovering a recurring pattern**: if you find yourself doing the same thing a third time, it belongs in MEMORY.
- **After a session where infra or environment behaviour was clarified**: future you will not remember.

## When to Read

- At the start of every `/dev-1-plan`, `/dev-3-run`, `/dev-4-qa`, `/fix`, and `/audit`.
- Before touching any area that has been touched before — MEMORY may have relevant gotchas.
- Before making an architecture decision — MEMORY may record a prior decision that applies.

## Keeping It Clean

- Remove entries that are no longer true (fixed bugs, changed behaviour, resolved constraints).
- If an entry has been superseded by a better understanding, rewrite it — don't append a correction below it.
- Keep entries short. One paragraph max. If it needs more, the knowledge belongs in a skill file, not MEMORY.
