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

3. **Run tests:**
   ```bash
   make test
   ```

## Available Commands

- `make build` - Build the development Docker image
- `make up` - Start the development container
- `make down` - Stop the development container
- `make shell` - Open a shell in the development container
- `make test` - Run tests
- `make test-cov` - Run tests with coverage report
- `make lint` - Run linting checks (flake8, mypy)
- `make format` - Format code with black
- `make clean` - Clean up containers and images
- `make logs` - Show container logs
- `make run` - Run the application in development mode

## Development Features

### Hot Reload
The source code is mounted as a volume, so changes are reflected immediately without rebuilding the container.

### Debugging
- **VS Code**: The container includes gevent for async debugging
- **Debug port**: Port 5678 is exposed for remote debugging
- **Logs**: Development logs are available in the `logs/` directory

### Testing
- **Unit tests**: Run with `make test`
- **Coverage**: Generate HTML coverage report with `make test-cov`
- **Linting**: Check code quality with `make lint`

### Code Quality
- **Formatting**: Use `make format` to format code with black
- **Type checking**: mypy is included for static type checking
- **Linting**: flake8 for code style checking

## Environment Variables

Copy `env.example` to `.env` and adjust the values:

```bash
cp env.example .env
```

Key variables:
- `LOGGER_LEVEL=DEBUG` - Enable debug logging
- `UPDATE_INTERVAL=60` - Faster updates for testing
- `HOSTS_CONFIG_FILE_PATH` - Path to your test hosts configuration

## Project Structure

```
dev/
├── Dockerfile          # Development container definition
├── docker-compose.yaml # Development services
├── dev-requirements.txt # Development dependencies
├── Makefile           # Development commands
├── env.example        # Environment variables template
├── README.md          # This file
└── logs/              # Development logs (created automatically)
```

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
cd /app
python -m pytest test/ -v
```

### Permission issues
```bash
sudo chown -R $USER:$USER .
```
