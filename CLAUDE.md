# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 5. Language

**All written artifacts are in English. Responses follow the user's language.**

- Code, comments, commit messages, documentation, task files, plan files: always English.
- Responses: use English by default. If the user writes in another language, reply in that language.

## 6. Git Workflow

**ALWAYS run the `git-conventions` skill before creating any commit or branch.**

## 7. Development Workflow

Three paths depending on the type of work. When in doubt, use the simplest one that fits.

| Situation | Path |
|-----------|------|
| New feature with multiple layers or non-trivial design | `/dev-1-plan` → `/dev-2-tasks` → `/dev-3-run` → `/dev-4-qa` → `/push` |
| Bug fix or small isolated change | `/fix` → `/push` |
| Consistency audit of a code area | `/audit` → `/push` |

Task files live in `docs/tasks/`. Plan files live in `docs/plans/`.

### Branch and commit conventions

- The feature branch is defined in `/dev-1-plan` and created automatically when the first task runs (`/dev-3-run`), branching from `develop` if it exists, otherwise from `main`/`master`.
- **Commit once per feature** — at the end of the full cycle (`/push`), after all tasks are approved. Do not commit after individual tasks unless the user explicitly requests it.

## 8. Project Structure

All application code lives in a single repository:

```
ovh-dyndns-client/
  docker-compose.yaml     # production — pre-built image, no bind mounts
  dev/
    docker-compose.yaml   # development — local build, bind mounts, live reload
    Dockerfile
  src/                    # Python application source code
  test/                   # Unit and integration tests
  e2e/                    # End-to-end tests (Playwright)
  scripts/                # Developer tooling scripts
  docs/                   # Documentation, plans (docs/plans/), tasks (docs/tasks/)
  CLAUDE.md
  MEMORY.md
```

### Two compose files, one source tree

- **`docker-compose.yaml`** (root): production. Uses the pre-built Docker Hub image (`cibrandocampo/ovh-dyndns-client:stable`), `restart: unless-stopped`. No bind mounts.
- **`dev/docker-compose.yaml`**: development. Builds from local Dockerfile, bind-mounts `src/` for live reload. Service: `ovh_dyndns_dev`, available at `http://localhost:8000`.

See `dev-workflow` skill for all specific commands (tests, lint, E2E, etc.).

## 9. Docker-First

**The user's machine is sacred. Never install or run project dependencies on the host.**

- NEVER run language runtimes directly on the host: no `python`, `pip`, etc.
- NEVER install project dependencies on the host: no `pip install`, etc.
- ALL project commands go through Docker: `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev <command>`
- The only tools allowed on the host are: `docker`, `git`, `gh`, and other system-level tools explicitly listed in `dev-workflow`.

**Why**: dependency conflicts, version mismatches, and environment drift are eliminated. What runs in Docker is exactly what runs in production.

Exceptions must be explicitly documented in the `dev-workflow` skill with a justification.

## 10. Testing

**ALWAYS consult the `test-discipline` skill before writing or debugging any test.**

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
