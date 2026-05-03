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
