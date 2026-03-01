---
name: run-tests
description: Run the project test suites. Use after making code changes to verify nothing is broken. Triggers when the user asks to run tests, verify changes, or after completing an implementation task.
---

# Running Tests — ovh-dyndns-client

## Critical rule

**NEVER run tests on the host.** Always use the `ovh_dyndns_dev` container via `dev/docker-compose.yaml`.

## Ensure the dev environment is running

```bash
docker compose -f dev/docker-compose.yaml ps
```

If the container is not running:
```bash
docker compose -f dev/docker-compose.yaml up -d
```

## Unit tests (pytest)

```bash
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/ -v
```

Run a specific module:
```bash
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/test_api.py -v
```

Run a specific test by name:
```bash
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/test_api.py::TestClassName::test_method_name -v
```

## Tests with coverage

```bash
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/ --cov=. --cov-report=term-missing
```

The minimum threshold in CI is **70%**. To verify locally:
```bash
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/ --cov=. --cov-report=term-missing --cov-fail-under=70
```

## E2E tests (Playwright — Docker, NOT host)

Playwright runs in its own Docker image (`e2e/Dockerfile`). It uses `--network host` to
reach the app at `localhost:8000`. Requires the dev app to be running first.

**Build the image** (only once, or after changing `e2e/package.json`):
```bash
docker build -f e2e/Dockerfile -t ovh-dyndns-e2e ./e2e
```

**Run all tests:**
```bash
docker run --rm --network host \
  -e E2E_USERNAME=admin \
  -e E2E_PASSWORD=<password> \
  ovh-dyndns-e2e npx playwright test
```

**Run a specific spec:**
```bash
docker run --rm --network host \
  -e E2E_USERNAME=admin \
  -e E2E_PASSWORD=<password> \
  ovh-dyndns-e2e npx playwright test tests/auth.spec.js
```

The password is set as an environment variable in `dev/docker-compose.yaml` or in the project `.env`.

## Verification workflow after a change

Always run unit tests before committing:

```bash
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/ -v
```

If they pass, the change is safe to commit.
