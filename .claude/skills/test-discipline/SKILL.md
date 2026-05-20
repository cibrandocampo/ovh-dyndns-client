---
name: test-discipline
description: Testing discipline — write strict tests, fail hard when they reveal bugs, diagnose and fix the root cause (code, infra, or test), then re-run until green. Use whenever writing or running tests (unit, integration, E2E), debugging a failing test, or tempted to reach for `test.skip` / weakened assertions / "known pre-existing failure" labels.
---

# Test Discipline

Tests are the safety net for a product going to production with real users.
A test that is softened to pass while prod is broken is worse than no test
at all — it actively lies.

## Core Principles

1. **One test = one concept.** Multiple `expect()` calls are fine if they
   validate the same concept. If you need "and" to name the test, split it.
2. **Fail hard, never softly.** If a test reveals a bug in the app (not
   in the test), the test must fail until the bug is fixed. Do **not**
   comment the assertion, loosen it, skip the test, or label the failure
   "known / pre-existing / flaky" just to move on.
3. **Diagnose root cause before changing anything.** Write a minimal
   reproducer that isolates the exact signal before editing code.
4. **Fix at the right layer.** A test failure can originate in:
   - The test itself (bad selector, wrong assumption, stale fixture).
   - The app code (real regression / gap in the feature).
   - The infrastructure (dev vs prod build, caching, stale modules, env mismatch).
   Identify the layer first, then fix there. Do not paper over an app
   bug with a test tweak.
5. **Re-run until deterministically green.** At least 3 consecutive
   runs without `--retries` before declaring the task done. One pass
   is not proof — timing races hide inside a single success.

## Required Workflow When a Test Fails

Step through these in order. Do not skip steps, even if the fix "looks obvious".

1. **Read the failure.** The error message, the stack, the call log,
   the screenshot / video attachment for E2E. Do not guess from the test title alone.
2. **Reproduce deterministically.** Run the failing test in isolation.
   If it fails intermittently, treat it as a race — don't retry until it passes.
3. **Classify the layer.** Is it:
   - **Test drift**: selector / fixture / copy changed — fix in the test.
   - **App bug**: the behaviour the test asserts is actually broken — fix in app code.
   - **Infra mismatch**: dev vs prod build behaviour, caching issues, stale modules — fix the infra.
4. **Apply the minimal fix.** Touch only what the diagnosis pointed to. Do not bundle unrelated cleanups.
5. **Re-run the failing test isolated.** Expect green.
6. **Run the full suite.** Ensure no regression elsewhere. If any regression appeared, stop and repeat from step 1 for that test.
7. **Run 3 more times back-to-back** without retries to catch races.
8. **Document the fix and decision** in the task file's `Execution evidence` block, including *which layer was wrong and why*.

## Forbidden Patterns

- `test.skip("TODO", ...)` without an open bug / follow-up task ID.
- `expect(...).toBeTruthy()` where `toEqual(specific)` would work — vague asserts hide regressions.
- Increasing timeout to "make the test pass" when a real race exists.
- Catching and ignoring errors inside a test to avoid a failure.
- Editing the assertion until it matches current (wrong) behaviour without understanding why.
- Labeling a failure "pre-existing / not our code" to move on.
  There is no such thing — the suite is your responsibility end to end.
- Merging with any test skipped or failing. Zero exceptions.

## When the Test Reveals an Infra Issue

If the failure points to infrastructure (build pipeline, caching, env mismatch):

1. Document the exact symptom and the infra gap it exposed.
2. Fix the infra (don't paper over it in the test).
3. Record the diagnosis in `MEMORY.md` under "Gotchas" so future work doesn't re-learn the same lesson.

## When the Test Reveals a Real App Bug

1. Stop the task — the test cannot pass.
2. Escalate in conversation: summarise the bug, its blast radius, and a proposed fix. Ask the user if the fix is in scope for this task or should be a separate bug task.
3. If the user approves fixing it here: apply the fix, link it in the task's `Execution evidence` under a "Feature gap closed" subsection, and continue.
4. If the user wants a separate task: write the bug up, leave the failing test in place, and stop the task. Do not comment the test out.

## Anti-Pattern Checklist Before Declaring Done

- [ ] Every test is atomic (one concept / one behaviour).
- [ ] Every failure I saw was **diagnosed** (not just patched away).
- [ ] The assertion is specific — not `toBeTruthy` or `expect.anything()`.
- [ ] No `test.skip`, no commented assertions, no loosened timeouts.
- [ ] Three consecutive green runs without `--retries`.
- [ ] Every infra gotcha I hit is in MEMORY.md if it could bite next time.
- [ ] Evidence table in the task file references **real command output**, not prose.

## Why This Matters

A false-negative test — one that passes while the feature is broken — creates direct user impact. The cost of strict discipline now is much smaller than the cost of a regression hitting real users later.
