---
name: ci
description: GitHub Actions CI conventions — pipeline structure, Docker-first testing, Docker image publishing, and weekly rebuilds. Use when creating or modifying CI workflows.
---

# CI — GitHub Actions

## Philosophy

The same Docker image that runs locally also runs in CI. No native language runtimes on the runner — no `setup-python`, no `pip`. Every test and lint command goes through `docker compose -f dev/docker-compose.yaml`, exactly as it does on the developer's machine. This eliminates the "works on my machine" class of CI failures.

Coverage files written by the test command appear on the host automatically because the dev compose bind-mounts `src/`. No extraction step needed.

---

## Workflow Structure

Two workflows. Each has a single responsibility.

### 1. `build-on-changes.yml` — test and build on every push and PR

**Triggers**: push to `main`, PR targeting `main`, release published.

**Job graph**:

```
test ──→ build-push
```

- Test job runs on every push and PR.
- Build/push runs only after tests pass, and only on `push` to `main` or `release` (not on PRs).

```yaml
build-push:
  needs: [test]
  if: github.event_name == 'push' || github.event_name == 'release'
```

### 2. `update-python.yml` — rebuild images without cache

**Trigger**: cron (weekly, Monday 06:00 UTC).

Rebuilds the production Docker image with `no-cache: true` to pick up base image patches and transitive dependency fixes. Does not run tests — the code has not changed.

---

## Test Job

### Pattern

```
1. checkout
2. create .env from .env.example
3. docker compose -f dev/docker-compose.yaml build ovh_dyndns_dev
4. docker compose -f dev/docker-compose.yaml run --rm --no-deps ovh_dyndns_dev ruff check .
5. docker compose -f dev/docker-compose.yaml run --rm --no-deps ovh_dyndns_dev ruff format --check .
6. docker compose -f dev/docker-compose.yaml run --rm ovh_dyndns_dev python -m pytest test/ --cov=. --cov-report=xml --cov-fail-under=70
7. upload coverage to Codecov
```

**`--no-deps` for lint**: lint does not need the database or scheduler. Pass `--no-deps` to skip starting dependency services.

**No `--no-deps` for tests**: the app may rely on container startup behaviour; omit it for the full test run.

### Environment variables in CI

The dev compose reads environment from the container definition. In CI, create `.env` from `.env.example`:

```yaml
- name: Create env file
  run: cp .env.example .env
```

Secrets (OVH credentials, JWT secrets) go in GitHub Actions secrets, not in `.env.example`.

### Coverage extraction

Because `dev/docker-compose.yaml` bind-mounts `src/`, any file the test command writes to the working directory appears on the host automatically. Upload `coverage.xml` directly with `codecov/codecov-action`.

---

## Build / Push Job

Builds the production image and pushes it to Docker Hub. Uses `docker/build-push-action` with multi-platform builds and GHA layer caching.

```yaml
build-push:
  needs: [test]
  if: github.event_name == 'push' || github.event_name == 'release'
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: docker/setup-qemu-action@v3
    - uses: docker/setup-buildx-action@v3
    - uses: docker/login-action@v3
      with:
        username: ${{ secrets.DOCKERHUB_USERNAME }}
        password: ${{ secrets.DOCKERHUB_TOKEN }}
    - name: Docker meta
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: cibrandocampo/ovh-dyndns-client
        tags: |
          type=raw,value=latest,enable=${{ github.ref == 'refs/heads/main' }}
          type=raw,value=stable,enable=${{ github.event_name == 'release' }}
          type=semver,pattern={{version}},enable=${{ github.event_name == 'release' }}
    - uses: docker/build-push-action@v6
      with:
        context: .
        platforms: linux/amd64,linux/arm64
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
```

### Image tagging strategy

| Event | Tags applied |
|-------|-------------|
| Push to `main` | `latest` |
| Release published | `stable`, `x.y.z` (semver) |
| Weekly rebuild | `latest` (no new tag) |

---

## Codecov Integration

```yaml
- uses: codecov/codecov-action@v5
  with:
    token: ${{ secrets.CODECOV_TOKEN }}
    files: coverage.xml
    fail_ci_if_error: false
    verbose: true
```

`fail_ci_if_error: false` — Codecov outages must never block merges.

---

## Required Secrets

| Secret | Where to get it |
|--------|----------------|
| `CODECOV_TOKEN` | codecov.io → repository settings |
| `DOCKERHUB_USERNAME` | Docker Hub account username |
| `DOCKERHUB_TOKEN` | Docker Hub → Account Settings → Personal Access Tokens |
