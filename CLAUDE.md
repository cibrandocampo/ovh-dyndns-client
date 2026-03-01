# ovh-dyndns-client — instrucciones para Claude Code

## Entorno de desarrollo: SIEMPRE usar Docker

**NUNCA ejecutes código Python directamente en el host.**
Usa siempre el contenedor de desarrollo `ovh_dyndns_dev` definido en `dev/docker-compose.yaml`.
Este compose usa bind mounts sobre `src/`, por lo que los cambios en archivos locales son visibles
de inmediato dentro del contenedor — no hace falta reconstruir la imagen.

### Comandos de referencia

| Tarea | Comando |
|---|---|
| **Tests** | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/ -v` |
| **Tests con cobertura** | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/ --cov=. --cov-report=term-missing` |
| **Lint** | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff check .` |
| **Format check** | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff format --check .` |
| **Format (aplicar)** | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff format .` |
| **Shell** | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev bash` |
| **Tests e2e** | ver skill `run-tests` |

Si el entorno dev no está levantado, arrancarlo con:
```bash
docker compose -f dev/docker-compose.yaml up -d
```

### Por qué NO usar el `docker-compose.yaml` raíz

El `docker-compose.yaml` raíz es de **producción** — usa la imagen publicada en Docker Hub
(`cibrandocampo/ovh-dyndns-client:stable`). Los cambios locales no se reflejan sin hacer un
build y push completo.
El `dev/docker-compose.yaml` es el correcto para desarrollo: monta el código fuente como volumen.
