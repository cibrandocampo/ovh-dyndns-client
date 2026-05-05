# Docs Alignment v5 — sincronizar superficies de documentación tras el hardening

## Context

La v5.0.0 introdujo cambios de seguridad (encryption-at-rest con Fernet, JWT
secret persistido, `must_change_password` enforcement, rate limiting) y
limpieza de comportamiento por defecto (auto-generación de secrets bajo
`data/`). El código y `docs/CONFIGURATION.md` están al día, pero **otras tres
superficies de documentación se han quedado atrás**:

1. **`env.example`** — todavía lista solo `JWT_SECRET` con un comentario
   engañoso ("recommended to change in production"). Faltan variables que
   un self-hoster espera ver: `ENCRYPTION_KEY`, `ADMIN_USERNAME`,
   `ADMIN_PASSWORD`, `JWT_EXPIRATION_HOURS`. Es el primer fichero que copia
   un usuario nuevo, y hoy le da una imagen incorrecta del modelo de
   configuración v5 (auto-generación + override opcional).

2. **Quick-start del README + snippet de la landing
   (`site/src/components/SelfHost.astro`)** — divergen del
   `docker-compose.yaml` de producción del repo: usan `restart: always`,
   no incluyen `init: true` ni `healthcheck`. La inconsistencia es
   pequeña pero confunde: tres versiones distintas del mismo compose en
   tres documentos.

3. **`docs/API.md`** — no menciona los nuevos rate limits (`5/min` login,
   `10/min` change-password, respuesta `429`) y no lista el endpoint
   `GET /api/version` que existe desde el commit del despliegue del site.

Es trabajo puramente documental, sin cambios de código de producción.
Bajo coste y alto retorno: deja las cuatro superficies hablando con la
misma voz y elimina ruido para futuros revisores.

---

## Decisions confirmed with user

| Topic | Decision |
|-------|----------|
| Alcance | Cuatro superficies en un mismo PR: `env.example`, quick-start de `README.md`, snippet `site/src/components/SelfHost.astro`, `docs/API.md`. |
| Fidelidad del quick-start | **100% sincronizado** con el `docker-compose.yaml` de producción: `init: true`, `restart: unless-stopped`, `healthcheck`. Manteniendo el bind mount directo `./data:/app/data` (sin la indirección de named volume del compose raíz, para no complicar el primer arranque). |
| `env.example` | Mirror de la sección "Example .env File" de `docs/CONFIGURATION.md` (líneas 125-147). Una sola fuente canónica para el ejemplo `.env`, copiada en `env.example`. |
| Profundidad del plan | Plan completo formal con tareas posteriores via `/dev-2-tasks`. |

---

## Design proposal

### 1. `env.example` — mirror de CONFIGURATION.md

Reescribir `env.example` para que coincida verbatim con el bloque
`## Example .env File` de `docs/CONFIGURATION.md`. Todas las variables
relevantes aparecen, con los defaults documentados como comentarios y los
secrets opcionales marcados explícitamente como auto-generados.

Nuevo contenido (esquemático — la versión final irá en la tarea):

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

Justificación de qué se incluye y qué no:

- Se omite `LOGGER_NAME` (en la tabla de CONFIGURATION.md pero raramente
  customizado; el ejemplo de CONFIGURATION.md ya lo omite — mantener
  consistencia).
- Se omite `JWT_EXPIRATION_HOURS` (existe en la tabla pero es un tuning,
  no parte del setup mínimo). Si en el futuro se considera necesario,
  añadir como comentario.
- Se omite `DATA_DIR` y `DATABASE_PATH` (rutas internas del contenedor;
  CONFIGURATION.md las marca como "Override only for tests").

Riesgo gestionado: el comentario `# JWT_SECRET=` (vacío, comentado) deja
claro que la línea está disponible para override, pero por defecto no se
debe establecer. Esto refleja exactamente el modelo v5.

### 2. Quick-start de README + landing — sincronizado con prod

Reemplazar el bloque YAML del quick-start del README (`README.md:83-96`)
y el `snippet` de `site/src/components/SelfHost.astro:2-13` por la
versión del `docker-compose.yaml` de producción del repo, **con bind
mount directo** (sin named volume):

```yaml
services:
  ovh-dyndns-client:
    image: cibrandocampo/ovh-dyndns-client:stable
    container_name: ovh-dyndns-client
    init: true
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

**Por qué bind mount directo en quick-start, no la versión con named
volume del repo**: la indirección via `volumes: ovh-dyndns-data:` con
`driver_opts: type: none, o: bind` aporta cero al primer-uso y mete
ruido conceptual. El usuario solo necesita "una carpeta del host
montada en `/app/data`". El compose de producción puede mantener su
forma actual, pero el quick-start expone el modelo mental más simple.

**Para la landing (`SelfHost.astro`)**: el snippet vive en una constante
`snippet` de TypeScript dentro del componente, así que el cambio es
sustituir la string. El estilo de los pasos (`# 1. Create
docker-compose.yaml`, `# 2. Start it`, `# 3. Open http://localhost:8000`)
se conserva — solo cambia el contenido del `cat > docker-compose.yaml
<<'YAML' ... YAML`.

### 3. `docs/API.md` — rate limits + endpoint version

Dos cambios mínimos y locales:

- **Endpoint `/api/version`**: añadir fila en la tabla de endpoints
  (`docs/API.md:44-58`), después de `/health`. Documentar como público
  (sin auth), devuelve `{"version": "<APP_VERSION>"}`.
- **Rate limits**: añadir nota corta al final de la sección
  "Authentication" (después de `### Change Password`), enlazando a
  `docs/CONFIGURATION.md#rate-limiting` para el detalle. Algo como:

  > **Rate limiting**: `/api/auth/login` está limitado a 5 req/min por
  > IP, `/api/auth/change-password` a 10 req/min por IP. Excederlo
  > devuelve `429 Too Many Requests`. Ver
  > [Rate limiting](CONFIGURATION.md#rate-limiting).

  No duplicar la tabla completa que ya está en CONFIGURATION.md — un
  enlace mantiene una única fuente de verdad.

Opcionalmente, añadir mención breve de `403 Password change required`
como respuesta posible cuando `must_change_password=true`. Pequeño,
mantiene el documento honesto sobre los flujos del backend.

---

## Scope

### What is included

- Reescribir `env.example` espejo de la sección `## Example .env File`
  de `docs/CONFIGURATION.md`.
- Sincronizar el bloque YAML del quick-start del `README.md` con el
  `docker-compose.yaml` de producción (bind mount directo).
- Sincronizar la constante `snippet` de
  `site/src/components/SelfHost.astro` con el mismo bloque YAML.
- Añadir fila `GET /api/version` a la tabla de endpoints de
  `docs/API.md`.
- Añadir nota de rate limiting en `docs/API.md` (con enlace a
  CONFIGURATION.md).
- Añadir nota corta de `403 Password change required` en `docs/API.md`.

### What is NOT included

- Cambios en código de producción (`src/`).
- Cambios en `docs/CONFIGURATION.md` (es la fuente canónica y ya está
  correcta).
- Cambios en el `docker-compose.yaml` raíz (la indirección via named
  volume no es ideal, pero ese es otro debate y rompería `DATA_PATH`
  para usuarios existentes).
- Modificaciones en otras secciones del `README.md` fuera del bloque
  YAML del quick-start.
- Cambios en otros componentes de la landing (`Hero.astro`,
  `HowItWorks.astro`, `FeatureCard.astro`).
- Tests nuevos. Estos cambios son documentales y los e2e existentes ya
  cubren el comportamiento descrito.
- Generar un `CHANGELOG.md`. El repo no lo tiene; mantenerlo fuera de
  alcance.

---

## Affected layers

| Layer | Impact |
|-------|--------|
| API (FastAPI) | **Ninguno** — solo se documenta lo que ya existe. |
| Application (services/ports) | Ninguno. |
| Domain (models) | Ninguno. |
| Infrastructure (OVH/ipify/SQLite) | Ninguno. |
| Tests | Ninguno. La cobertura existente (>96%) ya valida el comportamiento. |
| Docker / CI | Ninguno. El `docker-compose.yaml` raíz no se toca. |
| Docs (`README.md`, `docs/API.md`, `env.example`) | **Sí** — es el núcleo del cambio. |
| Site (`site/src/components/SelfHost.astro`) | **Sí** — sincronizar snippet self-host con la nueva forma del compose. |

---

## Implementation order

Orden lógico, agrupado por superficie. Cada paso es independiente y
verificable por separado.

1. **`env.example`** → reescribir el contenido espejo de CONFIGURATION.md.
2. **Quick-start de `README.md`** → reemplazar el bloque YAML
   (líneas 83-96) por la versión sincronizada con prod.
3. **`site/src/components/SelfHost.astro`** → reemplazar la constante
   `snippet` con el nuevo YAML embebido.
4. **`docs/API.md`** → añadir fila `/api/version` en la tabla, nota de
   rate limiting al final de "Authentication", nota de 403 password
   change required.
5. **Verificación local**:
   - `docker compose -f dev/docker-compose.yaml up -d` → arranca limpio.
   - `cd site && npm run build` → la landing build sigue funcionando.
   - Lectura cruzada: `env.example` ↔ `docs/CONFIGURATION.md` ↔
     `README.md` quick-start ↔ `SelfHost.astro` snippet → todos cuentan
     la misma historia.
6. **Commit y PR** siguiendo `git-conventions` (rama `docs/<slug>`,
   commit `docs: align env.example, quick-start and API docs with v5`,
   sin `Co-Authored-By`).

---

## Critical files

| File | Changes |
|------|---------|
| `env.example` | **Reescritura completa** (~20 líneas). Mirror del bloque "Example .env File" de `docs/CONFIGURATION.md`. |
| `README.md` (líneas 83-96) | Reemplazar bloque YAML del quick-start por versión sincronizada con prod (`init: true`, `restart: unless-stopped`, `healthcheck`). |
| `site/src/components/SelfHost.astro` (líneas 2-13) | Reemplazar la constante `snippet` con la nueva versión del compose YAML. El resto del componente no cambia. |
| `docs/API.md` | Añadir fila `GET /api/version` en la tabla de endpoints; añadir nota corta de rate limiting al final de la sección "Authentication" con enlace a `CONFIGURATION.md#rate-limiting`; añadir mención de `403 Password change required`. |

---

## Risks and considerations

- **Riesgo nulo en runtime**: ningún cambio en código de producción ni
  en tests. Los e2e siguen pasando porque el comportamiento no varía.
- **Build de la landing**: el cambio en `SelfHost.astro` es una constante
  string; Astro solo necesita rebuilder el sitio. El workflow
  `site-deploy.yml` se dispara con cualquier push a `main`, así que la
  publicación es automática.
- **Cache de imágenes en navegadores y bots**: la landing está cacheada
  agresivamente por GitHub Pages; el deploy puede tardar minutos en
  reflejarse para visitantes existentes. No es bloqueante.
- **Coherencia entre `env.example` y `docs/CONFIGURATION.md`**: una vez
  hechos espejos, cualquier futura adición de variable hay que aplicarla
  a ambos sitios. Considerar (fuera de alcance) un test simple que
  verifique que `env.example` ⊆ tabla de variables de
  `CONFIGURATION.md`.
- **Drift inverso**: si alguien edita `docker-compose.yaml` raíz en el
  futuro (cambia política `restart`, añade env vars), tendrá que
  actualizar también las dos copias del quick-start (README + landing).
  La indirección con named volume del compose raíz hace que NO sea
  factible incluir el quick-start como un fichero compartido; queda
  como duplicación consciente — bajo coste, fácil de mantener
  manualmente.

---

## Open design decisions

Ninguna. Las dos decisiones abiertas (alcance de la landing, fidelidad
del quick-start con prod) se cerraron en la fase de planificación y
están registradas en la tabla **Decisions confirmed with user**.
