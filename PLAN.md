# Plan: alinear ovh-dyndns-client con el flujo de nudge

Ejecutar en orden. Marcar cada tarea con `[x]` al completarla.

---

## 1. Limpiar `.claude/settings.local.json`

- [ ] Eliminar los JWT tokens hardcodeados que hay en el `allow` list
- [ ] Mantener solo permisos para Docker (`docker compose`, `docker build`, `docker run`) y `git`
- [ ] Eliminar las entradas `Bash(python3:*)` y `Bash(python -m pytest:*)` — en este proyecto no se ejecuta nada en el host

---

## 2. Crear `CLAUDE.md`

Instrucciones para Claude Code en este proyecto. Basarse en el equivalente de nudge.

- [ ] Regla principal: NUNCA ejecutar código Python directamente en el host
- [ ] Siempre usar el contenedor de desarrollo `ovh_dyndns_dev` definido en `dev/docker-compose.yaml`
- [ ] Tabla de comandos de referencia:

| Tarea | Comando |
|---|---|
| Tests | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/ -v` |
| Tests con cobertura | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/ --cov=. --cov-report=term-missing` |
| Lint | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff check .` |
| Format check | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff format --check .` |
| Format (aplicar) | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff format .` |
| Shell | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev bash` |
| E2E tests | `docker build -f e2e/Dockerfile -t ovh-dyndns-e2e ./e2e && docker run --rm --network host -e E2E_USERNAME=admin -e E2E_PASSWORD=<pass> ovh-dyndns-e2e npx playwright test` |

- [ ] Aclarar que `docker-compose.yaml` raíz es producción — no usarlo para desarrollo

---

## 3. Crear `.claude/skills/`

Tres skills. Misma estructura que nudge (carpeta con `SKILL.md` dentro).

### 3.1 `run-tests`

- [ ] Crear `.claude/skills/run-tests/SKILL.md`
- [ ] Regla crítica: NUNCA ejecutar en el host, siempre en el contenedor `ovh_dyndns_dev`
- [ ] Comando para verificar que el contenedor está corriendo
- [ ] Comando de tests unitarios (pytest)
- [ ] Comando de tests con cobertura
- [ ] Comando para un test específico (por módulo o por nombre)
- [ ] Sección de tests e2e: build de imagen + `docker run --network host`

### 3.2 `dev-workflow`

- [ ] Crear `.claude/skills/dev-workflow/SKILL.md`
- [ ] Cómo levantar el entorno dev (`make up` o docker compose)
- [ ] Referencia al Makefile en `dev/Makefile` y sus targets disponibles
- [ ] Cómo acceder al shell del contenedor
- [ ] Variables de entorno relevantes (qué hay en `.env`)

### 3.3 `git-conventions`

- [ ] Crear `.claude/skills/git-conventions/SKILL.md`
- [ ] Formato de commit: `<type>: <subject>` + cuerpo con bullet points
- [ ] Tipos válidos: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `style`
- [ ] Reglas: inglés siempre, sin punto final, imperativo, sin `Co-Authored-By`
- [ ] Referencia al pre-commit hook y cómo actuar si falla

---

## 4. Migrar linting de black/flake8/mypy a ruff

### 4.1 `pyproject.toml` (nuevo en raíz del proyecto)

- [ ] Crear `pyproject.toml` con sección `[tool.ruff]`:
  - `line-length = 120`
  - `target-version = "py312"`
  - `select = ["E", "F", "W", "I"]`
  - Ignorar líneas largas en migraciones si las hubiera
- [ ] Añadir sección `[tool.pytest.ini_options]`:
  - `testpaths = ["src/test"]`
  - `pythonpath = ["src"]`

### 4.2 `dev/dev-requirements.txt`

- [ ] Eliminar: `black`, `flake8`, `mypy`
- [ ] Añadir: `ruff>=0.4.0`
- [ ] Verificar que `pytest-mock` está incluido (ya debería estar)

### 4.3 `dev/Makefile`

- [ ] Actualizar target `lint`: reemplazar `flake8 . && mypy .` → `ruff check .`
- [ ] Actualizar target `format`: reemplazar `black .` → `ruff format .`
- [ ] Añadir target `lint-fix` (opcional): `ruff check --fix .`

### 4.4 Reconstruir imagen dev

- [ ] `docker compose -f dev/docker-compose.yaml build` para que instale ruff
- [ ] Verificar que `ruff check .` pasa en el contenedor

---

## 5. Pre-commit hook

### 5.1 `scripts/pre-commit`

- [ ] Crear `scripts/pre-commit` (bash, ejecutable)
- [ ] Verificar que el contenedor `ovh_dyndns_dev` está corriendo antes de continuar
- [ ] Step 1: `ruff check .` dentro del contenedor
- [ ] Step 2: `ruff format --check .` dentro del contenedor
- [ ] Mensajes de error claros con el comando de corrección

### 5.2 `scripts/install-hooks.sh`

- [ ] Crear `scripts/install-hooks.sh`
- [ ] Crear symlink `.git/hooks/pre-commit` → `scripts/pre-commit`
- [ ] Dar permisos de ejecución automáticamente

### 5.3 Instalar y verificar

- [ ] Ejecutar `bash scripts/install-hooks.sh`
- [ ] Hacer un commit de prueba para verificar que el hook funciona

---

## 6. Tests e2e con Playwright

### 6.1 Estructura de ficheros a crear

```
e2e/
├── Dockerfile
├── playwright.config.js
├── package.json
└── tests/
    ├── helpers.js
    ├── auth.spec.js
    ├── status.spec.js
    ├── hosts.spec.js
    ├── history.spec.js
    └── settings.spec.js
```

### 6.2 `e2e/Dockerfile`

- [ ] Basarse en `mcr.microsoft.com/playwright:v1.x-jammy`
- [ ] `WORKDIR /e2e`, copiar `package.json`, `npm install`, `npx playwright install chromium`
- [ ] Copiar el resto de ficheros

### 6.3 `e2e/package.json`

- [ ] Dependencia: `@playwright/test` (versión alineada con la imagen Docker)

### 6.4 `e2e/playwright.config.js`

- [ ] `baseURL`: `process.env.BASE_URL ?? 'http://localhost:8000'`
- [ ] `timeout`: 30000, `retries`: 1
- [ ] Reporter: `list` + `html` (open: never)
- [ ] Solo proyecto `chromium`

### 6.5 `e2e/tests/helpers.js`

- [ ] Exportar `CREDS` con `username` y `password` desde variables de entorno
- [ ] Exportar función `login(page)` que navega a `/login` y hace el flujo de autenticación

### 6.6 `e2e/tests/auth.spec.js`

- [ ] Página de login carga correctamente
- [ ] Credenciales incorrectas muestran error
- [ ] Credenciales correctas redirigen al dashboard
- [ ] Acceso sin autenticar redirige a login
- [ ] Cerrar sesión limpia la sesión

### 6.7 `e2e/tests/status.spec.js`

- [ ] La página de status muestra la IP actual
- [ ] La tabla de hosts se renderiza con columnas correctas
- [ ] El botón de forzar actualización de un host funciona
- [ ] Se muestra el próximo check programado
- [ ] El estado de cada host (ok/error) se refleja visualmente

### 6.8 `e2e/tests/hosts.spec.js`

- [ ] La página de hosts muestra el listado
- [ ] Se puede añadir un nuevo host (formulario, submit, aparece en lista)
- [ ] Se puede eliminar un host (confirm + desaparece de lista)

### 6.9 `e2e/tests/history.spec.js`

- [ ] La página de historial carga sin errores
- [ ] Se muestran entradas de historial (o mensaje de vacío si no hay)

### 6.10 `e2e/tests/settings.spec.js`

- [ ] La página de settings carga
- [ ] Se puede cambiar el intervalo de actualización y guardar
- [ ] Se puede cambiar el nivel de log y guardar

### 6.11 Verificar e2e en local

- [ ] `docker build -f e2e/Dockerfile -t ovh-dyndns-e2e ./e2e`
- [ ] Levantar la app en dev
- [ ] `docker run --rm --network host -e E2E_USERNAME=admin -e E2E_PASSWORD=<pass> ovh-dyndns-e2e npx playwright test`

---

## 7. Actualizar CI (`.github/workflows/build-on-changes.yml`)

- [ ] Añadir step de `ruff check .` antes del step de tests
- [ ] Añadir step de `ruff format --check .` antes del step de tests
- [ ] Combinar los dos steps de pytest en uno solo (evitar doble ejecución)
- [ ] Limpiar el nombre del workflow para que sea consistente con nudge (ej: `CI`)
- [ ] Añadir `cache: pip` en el setup de Python para acelerar builds
- [ ] Verificar que `build-and-push` sigue con `needs: test` correctamente

---

## 8. Actualizar weekly rebuild (`.github/workflows/update-python.yml`)

- [ ] Revisar que también incluye el step de ruff si se añade lint al job de test
- [ ] Verificar que la estructura es consistente con `build-on-changes.yml`

---

## Orden de ejecución recomendado

```
1 → 2 → 3 → 4 (con rebuild de imagen) → 5 → 6 → 7 → 8
```

Los pasos 1-3 son puramente de ficheros de configuración (sin riesgo).
El paso 4 requiere reconstruir la imagen dev.
El paso 5 depende del paso 4 (el hook llama a ruff dentro del contenedor).
El paso 6 es independiente y puede hacerse en paralelo con 4-5.
Los pasos 7-8 son los últimos porque consolidan todo en CI.
