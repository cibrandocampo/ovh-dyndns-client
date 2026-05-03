# T012 — Documentación (`CONFIGURATION.md`)

## Context

Las tasks T006–T011 cambian comportamiento visible al operador: `JWT_SECRET` se autogenera, aparece nueva variable opcional `ENCRYPTION_KEY`, `data/` ahora aloja secrets críticos, hay rate limit en login, e `ipify-py` ya no es dependencia. `docs/CONFIGURATION.md` actualmente miente en algún punto (dice `(auto-generated)` para `JWT_SECRET` cuando hasta hoy era un literal). Esta task pone la documentación al día.

Plan: [docs/plans/security-hardening.md](../plans/security-hardening.md), sección "What is included" → último bullet.

**Dependencies**: T007 (JWT_SECRET autogenerado), T008 (ENCRYPTION_KEY), T010 (rate limit), T011 (drop ipify).

## Objective

Que `docs/CONFIGURATION.md` describa con exactitud el comportamiento real de los secrets, las nuevas variables, el rate limiting, y las recomendaciones de seguridad actualizadas (proteger `data/`).

## Step 1 — Actualizar la tabla de Environment Variables

Editar `docs/CONFIGURATION.md`. La fila actual:

```
| `JWT_SECRET` | (auto-generated) | Secret key for JWT tokens |
```

Sustituir por una descripción precisa:

```
| `JWT_SECRET` | auto-generated and persisted at `data/.jwt_secret` | Secret key for JWT tokens. If not set, generated on first start (32-byte random) and saved with mode 0600. Override only if you need a fixed value across deployments. |
```

Añadir filas nuevas tras `JWT_EXPIRATION_HOURS`:

```
| `ENCRYPTION_KEY` | auto-generated and persisted at `data/.encryption_key` | Fernet key (44-byte base64) used to encrypt OVH host passwords at rest. Auto-generated on first start. Losing this file with encrypted hosts in DB makes credentials unrecoverable. |
| `DATA_DIR` | `/app/data` | Directory where SQLite, JWT secret and encryption key are stored. Override only for test or non-standard deployments. |
```

## Step 2 — Añadir sección "Persisted secrets and `data/` directory"

Tras la tabla de Environment Variables, añadir un nuevo bloque:

```markdown
## Persisted secrets and `data/` directory

The `data/` volume contains three files that the runtime may auto-generate
on first start:

| File | Purpose | Auto-generated if missing |
|------|---------|--------------------------|
| `dyndns.db` | SQLite database (hosts, users, history, settings) | Yes |
| `.jwt_secret` | 32-byte URL-safe random string used to sign JWT tokens | Yes |
| `.encryption_key` | Fernet key (44-byte base64) used to encrypt host passwords at rest | Yes (only if no encrypted hosts already exist) |

**Critical**: protect this directory.
- File permissions of `.jwt_secret` and `.encryption_key` are set to `0600`.
- Keep regular backups of the entire `data/` volume — losing `.encryption_key`
  with encrypted hosts in `dyndns.db` makes credentials unrecoverable.
- Never share these files. Never commit them to a repository.

If the runtime starts with `.encryption_key` missing **and** the database
contains encrypted hosts (rows with `password` prefixed by `enc:v1:`),
the container will refuse to start with a clear error message. Restore
the missing key file or set `ENCRYPTION_KEY` env var to recover.
```

## Step 3 — Actualizar el `.env` de ejemplo

En la sección "Example `.env` File", actualizar para reflejar que JWT_SECRET es opcional:

```ini
# Project
PROJECT_NAME=ovh-dyndns-client
DOCKER_OVH_VERSION=stable

# API
API_PORT=8000

# Data persistence (SQLite + secrets — protect this directory!)
DATA_PATH=./data

# Security — both auto-generated under data/ if not set.
# Set explicit values only if you need them fixed across deployments.
# JWT_SECRET=
# ENCRYPTION_KEY=

# Admin user — change immediately after first login!
ADMIN_USERNAME=admin
# ADMIN_PASSWORD=  # default 'admin', change required on first login

# Logging
LOGGER_LEVEL=INFO
```

## Step 4 — Añadir sección "Rate limiting"

Tras "Persisted secrets...", añadir:

```markdown
## Rate limiting

Authentication endpoints are rate-limited per client IP to mitigate brute-force
attempts:

| Endpoint | Limit |
|----------|-------|
| `POST /api/auth/login` | 5 requests per minute |
| `POST /api/auth/change-password` | 10 requests per minute |

Exceeding the limit returns `429 Too Many Requests`. Counters reset after
each minute window.

The implementation uses `slowapi` with in-memory storage. Counters are
reset whenever the container restarts.

**Reverse proxy note**: when running behind a reverse proxy (nginx, Traefik),
the limiter sees the proxy's IP as the source. Configure the proxy to set
`X-Forwarded-For` and adapt the limiter `key_func` if you need accurate
per-client limits. (Out of scope for the current release.)
```

## Step 5 — Actualizar "Security Recommendations"

La sección actual lista 4 puntos. Reescribirla para reflejar el nuevo modelo:

```markdown
## Security Recommendations

1. **Change default password** — default `admin/admin` is required to be
   changed on first login. Backend enforces this: any API call other than
   `/api/auth/change-password` returns `403` until the password is changed.
2. **Protect `data/`** — contains the SQLite database, JWT secret and
   encryption key. Loss or leak of these files is critical. Set strict
   filesystem permissions, exclude from non-encrypted backups, and never
   commit them.
3. **Use HTTPS** — put the service behind a reverse proxy (nginx, Traefik)
   with TLS. JWT tokens travel in the `Authorization` header; without TLS
   they are exposed to network sniffing.
4. **Restrict access** — limit network access to trusted IPs when possible.
5. **Rotate secrets** — to rotate `JWT_SECRET`, delete `data/.jwt_secret`
   and restart the container. All active tokens become invalid (users must
   log in again). To rotate `ENCRYPTION_KEY`, **first export plaintext
   passwords**, replace the key, then re-create hosts. There is no
   automatic re-encryption flow.
```

## Step 6 — Verificar consistencia con README

`README.md` referencia brevemente `JWT_SECRET` en el bloque "Quick Start". Verificar que sigue siendo coherente:

- Si el ejemplo de `docker-compose.yaml` del README incluye `JWT_SECRET=...`, mantenerlo (es válido como override).
- Si dice algo como "must be set" o "required", relajarlo a "optional — auto-generated if not set".

Cambio mínimo, solo si hay desalineamiento.

## DoD — Definition of Done

1. Tabla de Environment Variables refleja `JWT_SECRET` y `ENCRYPTION_KEY` con descripción precisa.
2. `DATA_DIR` documentada.
3. Nueva sección "Persisted secrets and `data/` directory" presente con los tres ficheros y advertencias.
4. `.env` de ejemplo actualizado: secrets comentados, `ADMIN_PASSWORD` comentada.
5. Nueva sección "Rate limiting" con tabla de límites y nota sobre reverse proxy.
6. "Security Recommendations" reescrita con los 5 puntos actuales.
7. README sin contradicciones con CONFIGURATION.md.
8. El documento parsea como Markdown válido (sin tablas rotas).

## Evidence to produce

| # | Description | Command | File | PASS condition |
|---|-------------|---------|------|----------------|
| 1 | Documento existe y se actualizó | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "wc -l /app/../docs/CONFIGURATION.md 2>/dev/null \|\| wc -l /docs/CONFIGURATION.md 2>/dev/null"` | `doc_size.txt` | número significativamente mayor que el original (~98 líneas) — al menos 130 |
| 2 | ENCRYPTION_KEY documentada | `grep -E 'ENCRYPTION_KEY' docs/CONFIGURATION.md` | `enc_key_doc.txt` | match no vacío en al menos dos zonas (tabla + sección) |
| 3 | Sección Rate limiting | `grep -E '^## Rate limiting' docs/CONFIGURATION.md` | `rate_limit_section.txt` | match no vacío |
| 4 | Sección Persisted secrets | `grep -E '^## Persisted secrets' docs/CONFIGURATION.md` | `secrets_section.txt` | match no vacío |
| 5 | README coherente | `grep -i 'jwt_secret' README.md` | `readme_jwt.txt` | sin afirmaciones tipo "required" o "must be set"; debe ser opcional o ejemplo |
| 6 | Markdown parsea | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -c "import re; t=open('/app/../docs/CONFIGURATION.md').read(); h=re.findall(r'^##? ', t, re.M); print(len(h), 'headings')"` (ajustar ruta si /app no expone docs/) | `md_parse.txt` | imprime ≥ 7 headings (Env Vars, Persisted secrets, Rate limiting, Security Recommendations, etc.) |

NOTA: si el dev container no monta `docs/`, ejecutar las verificaciones desde el host directamente con `grep` y `wc` (sin Docker).

## Files to create/modify

| File | Action |
|------|--------|
| `docs/CONFIGURATION.md` | MODIFY |
| `README.md` | MODIFY (Quick Start: replace explicit `JWT_SECRET=...` line with a comment pointing to CONFIGURATION.md) |

## Execution evidence

**Date**: 2026-05-03
**Modified files**:
- `docs/CONFIGURATION.md` — full rewrite. Environment Variables table now reflects the real behaviour (`JWT_SECRET` and `ENCRYPTION_KEY` auto-generated under `data/`, `DATA_DIR` documented, `ADMIN_PASSWORD` flagged as must-be-changed). Three new sections: "Persisted secrets and `data/` directory" (with file table and protection guidelines, plus the fail-fast behaviour when `.encryption_key` is missing), "Rate limiting" (per-endpoint limits, reverse-proxy caveat), and a rewritten "Security Recommendations" with five points covering forced password change, `data/` protection, HTTPS, network restriction and secret rotation. The `.env` example commented out the secrets and admin password to make the optional-by-default model obvious.
- `README.md` — Quick Start `docker-compose.yaml` snippet no longer hardcodes `JWT_SECRET=your-secret-key-min-32-chars-long!`. Replaced with a short comment explaining that both secrets are auto-generated under `./data` on first start and pointing readers to `docs/CONFIGURATION.md` for the override path. Keeps the simplest-deploy path as actually default-safe.

### Verification table

| # | Deliverable | Evidence file | Result |
|---|------------|---------------|--------|
| 1 | Document expanded substantially | `docs/tasks/evidence/T012/doc_size.txt` | PASS — `162` lines (≥ 130 required, 98 in original) |
| 2 | `ENCRYPTION_KEY` documented in multiple zones | `docs/tasks/evidence/T012/enc_key_doc.txt` | PASS — 4 mentions (env table, persisted-secrets section, `.env` example, rotation guidance) |
| 3 | "Rate limiting" section present | `docs/tasks/evidence/T012/rate_limit_section.txt` | PASS — `## Rate limiting` matched |
| 4 | "Persisted secrets and `data/`" section present | `docs/tasks/evidence/T012/secrets_section.txt` | PASS — `## Persisted secrets and `data/` directory` matched |
| 5 | README aligned (no "required"/"must be set") | `docs/tasks/evidence/T012/readme_jwt.txt` | PASS — only a comment line "JWT_SECRET and ENCRYPTION_KEY are auto-generated under ./data on first..." |
| 6 | Markdown parses with rich heading structure | `docs/tasks/evidence/T012/md_parse.txt` | PASS — `19 headings` (≥ 7 required) |
| 7 | Backend tests still green (regression guard) | `docs/tasks/evidence/T012/regression_tests.txt` | PASS — `221 passed, 98 warnings in 29.66s` |
| 8 | `ruff check` clean (regression guard) | `docs/tasks/evidence/T012/ruff_check.txt` | PASS — `All checks passed!` |

### Design decisions

- **README change is conservative.** Removed only the misleading explicit `JWT_SECRET=your-secret-key-min-32-chars-long!` line and replaced it with a comment that surfaces the new contract without expanding the Quick Start. Detailed semantics live in CONFIGURATION.md, which is what the comment points to.
- **`.env` example uses commented-out secrets.** Showing `# JWT_SECRET=` and `# ENCRYPTION_KEY=` (commented) communicates two things: the variables exist as overrides, and they're optional. A naked example value would have invited copy-paste of a hard-coded secret into production.
- **`ADMIN_PASSWORD` also commented in the example.** Operators that copy the file get a working zero-config setup with the default `admin/admin` (which the backend forces them to change on first login). Putting an explicit value here would have been worse — it'd suggest setting the password before first login, which T009 enforcement already covers.
- **No content rewrite on Settings, Docker Compose snippet, Monitoring sections.** They were correct and are preserved verbatim. Scope discipline: this task is documentation alignment, not a docs reflow.
- **Heading count of 19** comes from h2 + h3 throughout (Environment Variables, Settings, Persisted secrets, Example .env, Docker Compose, Rate limiting, Security Recommendations, Monitoring and Logs, View Logs, Normal Operation, IP Change…). Well above the soft target of 7 — the document gained five new sections.
