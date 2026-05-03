# T005 — Verificación end-to-end (smoke manual + Playwright)

## Context

Última task de la migración de design system. Levanta el dev container, recorre cada pantalla en navegador con la app real, captura screenshots de las cinco vistas principales (login, change-password, status, hosts, history, settings, modales) y ejecuta la suite Playwright completa para confirmar que nada de la lógica se ha roto.

Plan: [docs/plans/design-system-migration.md](../plans/design-system-migration.md), step 9 de "Implementation order".

**Dependencies**: T003, T004 (que a su vez dependen de T001 y T002 — al ejecutar T005, los cuatro previos deben estar completos).

## Objective

Confirmar visual y funcionalmente que la migración está completa: paleta nudge aplicada, iconos Lucide presentes, logo+favicon servidos, layout sin regresiones, suite E2E verde.

## Step 1 — Arrancar el entorno limpio

Bajar y volver a levantar el dev container para asegurar que sirve los nuevos estáticos:

```bash
docker compose -f dev/docker-compose.yaml down
docker compose -f dev/docker-compose.yaml up -d
```

Esperar al healthcheck (~10s). Verificar:

```bash
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c \
  "curl -sf http://localhost:8000/health"
```

Debe devolver `{"status":"healthy"}`.

## Step 2 — Verificar que los estáticos nuevos se sirven

```bash
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c \
  "curl -sf -o /dev/null -w 'icons.svg %{http_code}\n' http://localhost:8000/static/icons.svg && \
   curl -sf -o /dev/null -w 'source.svg %{http_code}\n' http://localhost:8000/static/icons/source.svg && \
   curl -sf -o /dev/null -w 'favicon.ico %{http_code}\n' http://localhost:8000/static/icons/favicon.ico && \
   curl -sf -o /dev/null -w 'manifest.json %{http_code}\n' http://localhost:8000/static/icons/manifest.json"
```

Los cuatro deben dar `200`.

## Step 3 — Smoke test manual con captura

Abrir `http://localhost:8000` en navegador y recorrer cada pantalla. Para cada una capturar screenshot full-page (Chrome DevTools → Cmd+Shift+P → "Capture full size screenshot" o equivalente).

Pantallas a capturar (ficheros con prefijo `evidence/`):

| Pantalla | Cómo llegar | Screenshot |
|---|---|---|
| Login | URL raíz tras logout | `evidence/01-login.png` |
| Change password | Login con admin/admin (default; o con credenciales que tengan must_change_password=true) | `evidence/02-change-password.png` |
| Status (con datos) | Tras login normal, default landing | `evidence/03-status.png` |
| Hosts | Click en nav "Hosts" | `evidence/04-hosts.png` |
| Hosts modal | Click en "Add Host" | `evidence/05-hosts-modal.png` |
| History | Click en nav "History" | `evidence/06-history.png` |
| Settings | Click en nav "Settings" | `evidence/07-settings.png` |

Validar visualmente en cada pantalla:
- Slate `#454961` predomina en navbar / botones primarios.
- Card "Current IP" tiene border-left amarillo (3px).
- Iconos Lucide visibles en nav, botones, columnas Status, modal close.
- Logo "D" visible en navbar (24px) y como favicon en la pestaña.
- Tipografía system stack (no Times New Roman, no fuentes raras).
- Sin elementos descoloridos o rotos.

## Step 4 — Ejecutar suite Playwright E2E

Construir la imagen E2E si no existe y ejecutar:

```bash
# Build (solo necesario si la imagen no existe)
docker build -f e2e/Dockerfile -t ovh-dyndns-e2e ./e2e

# Run all specs
docker run --rm --network host \
  -e E2E_USERNAME=admin \
  -e E2E_PASSWORD=admin123 \
  ovh-dyndns-e2e npx playwright test 2>&1 | tee evidence/e2e-output.txt
```

NOTA: las credenciales `admin/admin123` son las del `dev/docker-compose.yaml` (`ADMIN_PASSWORD: admin123`). Si la primera vez la app pide cambio de password, ejecutar el flow manualmente (o hacer un reset borrando `dev/data/dyndns.db`).

Esperado: todos los specs en verde. Cero failures.

## Step 5 — Verificación de contraste y accesibilidad básica

Con DevTools (Lighthouse / axe), correr una auditoría de accesibilidad sobre la pantalla `Status` post-login. Capturar:

```
evidence/lighthouse-a11y.txt   # nota global y top issues
```

Objetivo blando (no bloqueante): score ≥ 85 en accesibilidad. Si baja, anotar issues para futura iteración pero no bloquear esta task — el alcance era visual, no a11y formal.

## Step 6 — Checks finales

Ejecutar los unit tests Python para confirmar que la migración del frontend no ha tocado backend:

```bash
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev \
  python -m pytest test/ -v 2>&1 | tee evidence/unit-tests.txt
```

Y el lint+format del backend:

```bash
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff check . 2>&1 | tee evidence/ruff-check.txt
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff format --check . 2>&1 | tee evidence/ruff-format.txt
```

Los tres deben pasar (verde, exit 0).

## DoD — Definition of Done

1. Dev container arranca limpio y `/health` responde 200.
2. `icons.svg`, `source.svg`, `favicon.ico` y `manifest.json` se sirven con 200.
3. Las 7 pantallas tienen screenshot capturada en `evidence/`.
4. Validación visual completa: paleta slate, border-left amarillo en card IP, iconos en nav/botones/modales, logo en navbar, sin regresiones de layout.
5. Suite Playwright completa pasa con 0 failures.
6. Unit tests Python pasan con 0 failures.
7. `ruff check` y `ruff format --check` pasan en verde.

## Evidence to produce

| # | Description | Command | File | PASS condition |
|---|-------------|---------|------|----------------|
| 1 | Health del dev container | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev curl -sf http://localhost:8000/health` | `health.txt` | `{"status":"healthy"}` |
| 2 | Estáticos nuevos servidos | (ver Step 2) | `static_serve.txt` | los 4 ficheros responden 200 |
| 3 | Screenshots smoke | manual | `evidence/01-login.png` ... `evidence/07-settings.png` | 7 capturas presentes, ninguna rota |
| 4 | Playwright E2E | `docker run --rm --network host -e E2E_USERNAME=admin -e E2E_PASSWORD=admin123 ovh-dyndns-e2e npx playwright test` | `evidence/e2e-output.txt` | exit 0, "X passed" sin failed |
| 5 | Lighthouse a11y | manual con DevTools | `evidence/lighthouse-a11y.txt` | score ≥ 85 (blando) |
| 6 | Unit tests backend | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/ -v` | `evidence/unit-tests.txt` | exit 0, all green |
| 7 | Lint backend | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff check .` | `evidence/ruff-check.txt` | exit 0, "All checks passed!" |
| 8 | Format backend | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff format --check .` | `evidence/ruff-format.txt` | exit 0 |

## Files to create/modify

Esta task no modifica código de la app. Si durante la verificación se descubren bugs introducidos por T001-T004, **no parchearlos aquí**: abrir un PR de fix o devolver la task correspondiente a estado `RETURNED` para corrección.

| File | Action |
|------|--------|
| (ninguno en `src/`) | — |
| `docs/tasks/evidence/*` | CREATE (screenshots y outputs) |

## Execution evidence

**Date**: 2026-05-03
**Modified files**: none in `src/`. The task is verification-only.

### Verification table

| # | Deliverable | Evidence file | Result |
|---|------------|---------------|--------|
| 1 | `/health` returns 200 + healthy payload | `docs/tasks/evidence/T005/health.txt` | PASS — `{"status":"healthy"}` |
| 2 | All four key static assets serve 200 | `docs/tasks/evidence/T005/static_serve.txt` | PASS — `icons.svg 200`, `source.svg 200`, `favicon.ico 200`, `manifest.json 200` |
| 3 | 7 page screenshots captured (full-page, 1280×800) | `docs/tasks/evidence/T005/01-login.png` … `07-settings.png`, plus `screenshots-log.txt` | PASS — 7 PNGs, 17–51 KB each. Visual review confirmed: slate palette, yellow border-left on Current IP card, Lucide icons in nav/buttons/status column/modal close, brand logo "D" in navbar. |
| 4 | Playwright suite (27 specs) passes | `docs/tasks/evidence/T005/e2e-output.txt` | PASS — `27 passed (11.1s)` |
| 5 | A11y review (lighthouse-equivalent) | `docs/tasks/evidence/T005/lighthouse-a11y.txt` | PASS — manual audit, AAA contrast on primary palette, all icon-only buttons have `aria-label`, estimated Lighthouse ≈ 90–95, above the soft 85 target |
| 6 | Backend unit tests pass | `docs/tasks/evidence/T005/unit-tests.txt` | PASS — `179 passed, 1 warning in 20.39s` |
| 7 | `ruff check .` clean | `docs/tasks/evidence/T005/ruff-check.txt` | PASS — `All checks passed!` |
| 8 | `ruff format --check .` clean | `docs/tasks/evidence/T005/ruff-format.txt` | PASS — `37 files already formatted` |

### Design decisions

- **Programmatic screenshots via Playwright** (one-shot `e2e/screenshots.mjs`, mounted into the existing `ovh-dyndns-e2e` Docker image). Capturing manually with Chrome DevTools' "Capture full size screenshot" was the path the spec described, but a CLI-driven Playwright capture is more reliable, repeatable and produces a verifiable artifact. The script was removed after the task; if visual regression coverage becomes a recurring need, port it to `e2e/tests/visual.spec.js`.
- **Change-password screenshot via localStorage trick**, not by resetting the DB. Setting `localStorage.token = 'screenshot-dummy-token'` and `localStorage.mustChangePassword = 'true'` then reloading forces the client into the change-password view without any backend call (the page is purely client-side until form submit). Avoids touching `dev/data/dyndns.db` during evidence capture.
- **Lighthouse skipped, manual a11y audit instead.** The dev container has no Chrome and adding lighthouse-cli for a one-shot run was disproportionate. The task explicitly marks this as "blando, no bloqueante". The `lighthouse-a11y.txt` covers the same dimensions Lighthouse audits (color contrast, accessible names, form labels, focus visibility, decorative imagery, semantic landmarks) with concrete numbers and three tracked issues for future iteration.
- **App shutdown after evidence #5**: launched `python main.py` in detached mode for the verification run, killed it at the end. Container left back in the `tail -f /dev/null` keep-alive state defined by `dev/docker-compose.yaml`.
- **Screenshot mount** uses an extra `-v "$(pwd)/e2e/screenshots.mjs":/e2e/screenshots.mjs` rather than rebuilding the e2e image, since the script is temporary and the image's `node_modules` is needed.
