---
name: security
description: Security checklist to review before committing code. Use before any commit that adds or modifies user input handling, authentication, data access, API endpoints, dependencies, or file operations.
---

# Security

Run this checklist against your diff before committing. If any item fails, fix it — do not commit and flag it later.

## Secrets & Credentials

- [ ] No hardcoded passwords, API keys, tokens, or secrets in code or config files.
- [ ] No secrets in commit messages, comments, or log statements.
- [ ] Sensitive configuration comes from environment variables, not source code.
- [ ] `.env` files are in `.gitignore` and never committed.

## Input Validation

- [ ] All user input is validated at the boundary (type, length, format, range).
- [ ] Never trust data from external sources (HTTP requests, files, environment, query params).
- [ ] Validation happens server-side — client-side validation is UX only, not security.
- [ ] File uploads: validate type, size, and name. Never use the user-supplied filename directly.

## Injection

- [ ] No raw SQL with user input — use parameterised queries or ORM.
- [ ] No shell commands constructed from user input — if unavoidable, use safe APIs with argument lists, never string interpolation.
- [ ] No template rendering with unescaped user data (XSS).
- [ ] No `eval()`, `exec()`, or dynamic code execution with external input.

## Authentication & Authorisation

- [ ] Every endpoint that requires authentication actually checks it.
- [ ] Authorisation checks verify the caller owns or has permission to access the resource (not just that they are logged in).
- [ ] Sensitive operations require re-authentication or elevated checks where appropriate.
- [ ] No security-by-obscurity: hidden URLs or fields are not access control.
- [ ] CSRF protection is in place for any state-changing request made via browser (cookies/sessions). Token-based APIs using `Authorization` header are exempt.
- [ ] Rate limiting is applied to authentication endpoints (login, password reset, token refresh) and any expensive or sensitive operation.

## Data Exposure

- [ ] API responses do not leak internal fields, stack traces, or system information.
- [ ] Error messages are generic for the user; detail goes to server logs only.
- [ ] Sensitive fields (passwords, tokens, PII) are not serialised into responses or logs.
- [ ] Pagination and filtering respect authorisation — a user cannot enumerate records they don't own.

## Dependencies

- [ ] New dependencies are well-maintained, widely used, and necessary.
- [ ] No dependency added just for convenience when the standard library covers the need.
- [ ] Pinned versions in lockfiles are not blindly upgraded without reviewing the changelog.

## HTTP Security Headers (frontend / server)

- [ ] `Content-Security-Policy` is set and restricts `script-src` to known origins. No `unsafe-inline` or `unsafe-eval` unless explicitly justified.
- [ ] `X-Content-Type-Options: nosniff` is set.
- [ ] `X-Frame-Options: DENY` (or `SAMEORIGIN`) is set to prevent clickjacking.
- [ ] `Strict-Transport-Security` is set in production (HTTPS only).

## File & Path Handling

- [ ] User-supplied paths are validated and confined to an allowed directory (no path traversal).
- [ ] Temporary files are cleaned up and not world-readable.

## How to Apply

1. Run `git diff --staged` and read every changed line.
2. Go through the checklist above — each item takes seconds.
3. If anything is uncertain, err on the side of caution: ask before committing.
4. Document any accepted risk explicitly in a comment near the code and in the PR Notes section.
