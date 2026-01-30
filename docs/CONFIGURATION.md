# Configuration

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PROJECT_NAME` | `ovh-dyndns-client` | Container name |
| `DOCKER_OVH_VERSION` | `stable` | Docker image version |
| `API_PORT` | `8000` | API server port |
| `DATA_PATH` | `./data` | Path for SQLite database on host |
| `DATABASE_PATH` | `/app/data/dyndns.db` | Database file path inside container |
| `JWT_SECRET` | (auto-generated) | Secret key for JWT tokens |
| `JWT_EXPIRATION_HOURS` | `24` | Token expiration time in hours |
| `ADMIN_USERNAME` | `admin` | Default admin username |
| `ADMIN_PASSWORD` | `admin` | Default admin password |
| `LOGGER_NAME` | `ovh-dydns` | Logger name |
| `LOGGER_LEVEL` | `INFO` | Initial log level |

## Settings (Configurable via UI)

These settings can be changed through the web interface or API without restarting the container:

| Setting | Default | Range | Description |
|---------|---------|-------|-------------|
| Update Interval | `300` | 60-86400 | How often to check for IP changes (seconds) |
| Log Level | `INFO` | DEBUG, INFO, WARNING, ERROR, CRITICAL | Logging verbosity |

## Example `.env` File

```ini
# Project
PROJECT_NAME=ovh-dyndns-client
DOCKER_OVH_VERSION=stable

# API
API_PORT=8000

# Data persistence
DATA_PATH=./data

# Security (recommended to change in production)
JWT_SECRET=your-secure-random-secret-key
ADMIN_PASSWORD=your-secure-admin-password

# Logging
LOGGER_NAME=ovh-dydns
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

## Security Recommendations

1. **Change default password**: The default `admin/admin` credentials should be changed immediately
2. **Set JWT_SECRET**: Use a strong, random secret key in production
3. **Use HTTPS**: Put the service behind a reverse proxy (nginx, traefik) with TLS
4. **Restrict access**: Limit network access to trusted IPs if possible

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
