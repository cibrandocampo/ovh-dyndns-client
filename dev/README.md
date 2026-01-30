# Development Environment

This directory contains the development setup for the OVH DynDNS Client project.

## Quick Start

1. **Build and start the development environment:**
   ```bash
   make build
   make up
   ```

2. **Open a shell in the container:**
   ```bash
   make shell
   ```

3. **Run the application:**
   ```bash
   make run
   ```

4. **Run tests:**
   ```bash
   make test
   ```

## Available Commands

| Command | Description |
|---------|-------------|
| `make build` | Build the development Docker image |
| `make up` | Start the development container |
| `make down` | Stop the development container |
| `make shell` | Open a shell in the container |
| `make run` | Run the application |
| `make test` | Run tests |
| `make test-cov` | Run tests with coverage report |
| `make lint` | Run linting checks (flake8, mypy) |
| `make format` | Format code with black |
| `make logs` | Show container logs |
| `make clean` | Clean up containers and images |

## Environment Variables

Environment variables are configured in `docker-compose.yaml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `LOGGER_LEVEL` | `DEBUG` | Log level for development |
| `API_PORT` | `8000` | API server port |
| `DATABASE_PATH` | `/app/data/dyndns.db` | SQLite database path |
| `JWT_SECRET` | `dev-secret-key...` | JWT signing key |

## Development Features

### Hot Reload
The source code is mounted as a volume, so changes are reflected immediately without rebuilding.

### Debugging
- **VS Code**: The container includes gevent for async debugging
- **Debug port**: Port 5678 is exposed for remote debugging

### Testing
- **Unit tests**: `make test`
- **Coverage**: `make test-cov`
- **Linting**: `make lint`

## Troubleshooting

### Container won't start
```bash
make clean
make build
make up
```

### Tests failing
```bash
make shell
python -m pytest /app/test/ -v
```
