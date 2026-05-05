# Task index — ovh-dyndns-client

## Series T001–T005 — Design system migration (paleta, tipografía, iconos, logo)

Plan: [docs/plans/design-system-migration.md](../plans/design-system-migration.md)

| ID | Title | Dependencies | Status | QA |
|----|-------|-------------|--------|----|
| T001 | Crear sprite SVG con 17 iconos Lucide | — | Completed | — |
| T002 | Reescribir style.css con paleta nudge, tipografía y clases helper | — | Completed | — |
| T003 | Diseñar logo "D", generar set de assets PWA y wirear `<head>` | — | Completed | — |
| T004 | Insertar iconos Lucide en `index.html` y `app.js` | T001, T002 | Completed | — |
| T005 | Verificación end-to-end (smoke manual + Playwright) | T003, T004 | Completed | — |

### Execution order

```
T001 ──┐
T002 ──┼──→ T004 ──┐
       │           ├──→ T005
T003 ──────────────┘
```

T001, T002 y T003 son independientes y paralelizables. T004 necesita el sprite (T001) y la clase `.icon` ya en CSS (T002). T005 cierra cuando todo está integrado.

---

## Series T006–T012 — Security hardening (riesgos críticos 1–6)

Plan: [docs/plans/security-hardening.md](../plans/security-hardening.md)

| ID | Title | Dependencies | Status | QA |
|----|-------|-------------|--------|----|
| T006 | Migrar `python-jose` → `PyJWT` y adaptar tests | — | Completed | — |
| T007 | Módulo `infrastructure/secrets.py` (auto-generar JWT_SECRET y ENCRYPTION_KEY) | T006 | Completed | — |
| T008 | Cifrado at-rest de passwords OVH (Fernet) + migración idempotente | T007 | Completed | — |
| T009 | Enforcement de `must_change_password` (split de dependencies) | — | Completed | — |
| T010 | Rate limiting con `slowapi` en `/api/auth/*` | T009 | Completed | — |
| T011 | Timeouts en HTTP clients y drop de `ipify-py` | — | Completed | — |
| T012 | Documentación (`CONFIGURATION.md`) | T007, T008, T010, T011 | Completed | — |

### Execution order

```
T006 → T007 → T008 ───┐
                      │
T009 → T010 ──────────┤
                      ├─→ T012
T011 ─────────────────┘
```

Tres ramas paralelizables: auth-foundation (T006→T007→T008), auth-flow (T009→T010) y network resilience (T011). T012 cierra documentando los cambios visibles al operador.

---

## Series T013–T015 — Seed and screenshots pipeline

Plan: [docs/plans/seed-and-screenshots-pipeline.md](../plans/seed-and-screenshots-pipeline.md)

| ID | Title | Dependencies | Status | QA |
|----|-------|-------------|--------|----|
| T013 | Seed `scripts/seed.py` + dev compose mount + tests | — | Completed | — |
| T014 | Playwright screenshot capture (`e2e/screenshots.mjs`) | T013 | Completed | — |
| T015 | Orchestration: `Makefile` + `wait-for-health.sh` + regenerated PNGs | T013, T014 | Completed | — |

### Execution order

```
T013 ──→ T014 ──→ T015
```

Cadena lineal: la pipeline es producer → consumer → orchestrator.

---

## Series T016–T019 — Landing page (Astro + Tailwind, deployed to GitHub Pages)

Plan: [docs/plans/landing-page.md](../plans/landing-page.md)

| ID | Title | Dependencies | Status | QA |
|----|-------|-------------|--------|----|
| T016 | Astro + Tailwind scaffold (`site/`) + Base layout + public assets | — | Completed | — |
| T017 | Five components (Hero, HowItWorks, FeatureCard, SelfHost, Footer) + `index.astro` | T016 | Completed | — |
| T018 | Build pipeline (`copy-screenshots.mjs` + Makefile `site-dev` / `site-build`) | T017 | Completed | — |
| T019 | `site-deploy.yml` workflow + verify Pages URL responds 200 | T018 | Awaiting merge | — |

### Execution order

```
T016 ──→ T017 ──→ T018 ──→ T019
```

Cadena lineal: scaffold → componentes → build pipeline → deploy. Cada paso depende del anterior porque añade un layer concreto (estructura, contenido, assets, CI).

---

## Series T020–T022 — Docs alignment v5 (env.example, quick-start, API.md)

Plan: [docs/plans/docs-alignment-v5.md](../plans/docs-alignment-v5.md)

| ID | Title | Dependencies | Status | QA |
|----|-------|-------------|--------|----|
| T020 | Sincronizar `env.example` con `docs/CONFIGURATION.md` | — | Completed | — |
| T021 | Sincronizar snippet `docker-compose.yaml` en README quick-start + `site/src/components/SelfHost.astro` | — | Completed | — |
| T022 | Añadir rate limits, `GET /api/version` y nota 403 a `docs/API.md` | — | Completed | — |

### Execution order

```
T020 ──┐
T021 ──┼──→ (PR único: docs alignment v5)
T022 ──┘
```

Las tres tareas son independientes — tocan ficheros distintos sin solapamiento — y pueden ejecutarse en cualquier orden o en paralelo. Se cierran en un solo PR de docs.
