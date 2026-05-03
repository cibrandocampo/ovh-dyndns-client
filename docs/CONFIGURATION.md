# Configuration

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PROJECT_NAME` | `ovh-dyndns-client` | Container name |
| `DOCKER_OVH_VERSION` | `stable` | Docker image version |
| `API_PORT` | `8000` | API server port |
| `DATA_PATH` | `./data` | Path for the data volume on the host |
| `DATA_DIR` | `/app/data` | Directory inside the container that holds SQLite, JWT secret and encryption key. Override only for tests or non-standard deployments. |
| `DATABASE_PATH` | `/app/data/dyndns.db` | Database file path inside the container |
| `JWT_SECRET` | auto-generated and persisted at `data/.jwt_secret` | Secret used to sign JWT tokens. If unset on first start, a 32-byte URL-safe random string is generated and saved with mode `0600`. Override only when you need a fixed value across deployments. |
| `JWT_EXPIRATION_HOURS` | `24` | Token expiration time in hours |
| `ENCRYPTION_KEY` | auto-generated and persisted at `data/.encryption_key` | Fernet key (44-byte base64) used to encrypt OVH host passwords at rest. Auto-generated on first start. **Losing this file with encrypted hosts in the database makes those credentials unrecoverable.** |
| `ADMIN_USERNAME` | `admin` | Default admin username |
| `ADMIN_PASSWORD` | `admin` | Default admin password (must be changed on first login) |
| `LOGGER_NAME` | `ovh-dydns` | Logger name |
| `LOGGER_LEVEL` | `INFO` | Initial log level |

## Settings (Configurable via UI)

These settings can be changed through the web interface or API without restarting the container:

| Setting | Default | Range | Description |
|---------|---------|-------|-------------|
| Update Interval | `300` | 60-86400 | How often to check for IP changes (seconds) |
| Log Level | `INFO` | DEBUG, INFO, WARNING, ERROR, CRITICAL | Logging verbosity |

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
  with encrypted hosts in `dyndns.db` makes those credentials unrecoverable.
- Never share these files. Never commit them to a repository.

If the container starts with `.encryption_key` missing **and** the database
contains encrypted hosts (rows with `password` prefixed by `enc:v1:`),
the runtime refuses to boot and logs a clear remediation message. Restore
the missing key file or set the `ENCRYPTION_KEY` env var to the previous
value to recover.

## Migrating from a previous release

Upgrading from a release that stored OVH host passwords as plaintext is
**zero-touch**: pull the new image and restart. The runtime takes care
of generating the missing secrets and re-encrypting existing data on
first boot.

What happens, in order:

1. `init_db()` — idempotent; existing tables and rows survive.
2. `JWT_SECRET` resolution. If the env var is set, the same value is
   reused (active tokens stay valid). Otherwise, a 32-byte random
   string is generated and persisted at `data/.jwt_secret`; existing
   tokens become invalid and users will need to log in again.
3. Consistency check. If the database has rows with the `enc:v1:`
   prefix but no key is available, the container refuses to boot
   (see "Persisted secrets and `data/` directory" above). On a
   fresh upgrade there are no such rows, so this is a no-op.
4. `ENCRYPTION_KEY` resolution. Same precedence as `JWT_SECRET`: env
   var, then persisted file, then auto-generation into
   `data/.encryption_key` (mode `0600`).
5. **Boot-time password migration**. Every host whose `password` does
   not start with `enc:v1:` is encrypted in place with the key from
   step 4. The runtime logs a single line:

   ```
   Encrypted N legacy plaintext host password(s)
   ```

   On every subsequent boot the migration is a no-op (count `0`) and
   the line is suppressed.
6. Admin user check, scheduler thread, FastAPI server — unchanged.

After the first restart:

- No legible OVH password remains in `data/dyndns.db`.
- `data/.jwt_secret` and `data/.encryption_key` both exist (mode `0600`).
- Login flow now enforces `must_change_password`: an admin who never
  rotated the default `admin/admin` will get `403 Password change
  required` from every endpoint other than `/api/auth/change-password`
  until the password is changed.
- `/api/auth/login` is rate-limited (5/min/IP); `/api/auth/change-password`
  is rate-limited (10/min/IP).

### Operator action items

- **Back up `data/` immediately** after the upgrade and on a regular
  schedule. Losing `.encryption_key` while encrypted hosts exist makes
  those credentials unrecoverable.
- If the previous deployment used a weak hard-coded `JWT_SECRET` in
  `docker-compose.yaml`, this is a good moment to remove it and let
  the runtime auto-generate a strong one under `data/`.
- Behind a reverse proxy, rate-limit accuracy depends on
  `X-Forwarded-For` propagation. See "Rate limiting" below.

### Edge case: env-var key without a persisted file

If you start with `ENCRYPTION_KEY` set as an env var, the runtime uses
it and never writes `data/.encryption_key`. If you later remove the env
var without writing the file by hand, the next boot will detect
encrypted hosts but no key and fail-fast. Two safe options:

- Keep the env var permanently set, **or**
- Persist the same value to disk before removing the env var:

  ```bash
  echo -n "$ENCRYPTION_KEY" > data/.encryption_key && chmod 600 data/.encryption_key
  ```

## Example `.env` File

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

## Docker Compose

```yaml
services:
  ovh-dyndns-client:
    image: cibrandocampo/ovh-dyndns-client:${DOCKER_OVH_VERSION:-stable}
    container_name: "${PROJECT_NAME:-ovh-dyndns-client}"
    restart: always
    init: true
    env_file:
      - .env
    ports:
      - "${API_PORT:-8000}:8000"
    volumes:
      - ${DATA_PATH:-./data}:/app/data
```

## Rate limiting

Authentication endpoints are rate-limited per client IP to mitigate brute-force
attempts:

| Endpoint | Limit |
|----------|-------|
| `POST /api/auth/login` | 5 requests per minute |
| `POST /api/auth/change-password` | 10 requests per minute |

Exceeding the limit returns `429 Too Many Requests`. Counters reset after
each minute window.

The implementation uses `slowapi` with in-memory storage. Counters also
reset whenever the container restarts.

**Reverse proxy note**: when running behind a reverse proxy (nginx, Traefik),
the limiter sees the proxy's IP as the source. Configure the proxy to
forward the real client IP via `X-Forwarded-For` and adapt the limiter
`key_func` if you need accurate per-client limits. (Out of scope for the
current release.)

## Security Recommendations

1. **Change default password** — default `admin/admin` is required to be
   changed on first login. The backend enforces this: any API call other
   than `POST /api/auth/change-password` returns `403 Password change
   required` until the password is rotated.
2. **Protect `data/`** — contains the SQLite database, JWT secret and
   encryption key. Loss or leak of these files is critical. Set strict
   filesystem permissions, exclude from non-encrypted backups, and never
   commit them.
3. **Use HTTPS** — put the service behind a reverse proxy (nginx, Traefik)
   with TLS. JWT tokens travel in the `Authorization` header; without TLS
   they are exposed to network sniffing.
4. **Restrict access** — limit network access to trusted IPs when possible.
5. **Rotate secrets** — to rotate `JWT_SECRET`, delete `data/.jwt_secret`
   and restart the container; all active tokens become invalid (users
   must log in again). To rotate `ENCRYPTION_KEY`, **first export the
   plaintext passwords** (e.g. via the API), replace the key, then re-create
   the hosts. There is no automatic re-encryption flow.

## Monitoring and Logs

### View Logs

```bash
docker logs -f ovh-dyndns-client
```

### Normal Operation

```
2025-10-24T12:01:32+0000 (ovh-dydns) INFO | Executing DNS update controller
2025-10-24T12:01:32+0000 (ovh-dydns) INFO | Starting DNS update process
2025-10-24T12:01:32+0000 (ovh-dydns) INFO | Retrieved public IP: 83.34.148.172
2025-10-24T12:01:32+0000 (ovh-dydns) INFO | IP unchanged, skipping update
2025-10-24T12:01:35+0000 (ovh-dydns) INFO | DNS update completed successfully
```

### IP Change

```
2025-10-24T12:01:32+0000 (ovh-dydns) INFO | IP changed, updating hosts
2025-10-24T12:01:33+0000 (ovh-dydns) INFO | example.es | Update response: 200 good 83.34.148.173
```
