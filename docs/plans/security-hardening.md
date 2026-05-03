# Security Hardening — Riesgos críticos 1–6

## Context

Una revisión del proyecto identificó seis riesgos de seguridad que comprometen la postura del servicio en producción:

1. **`python-jose` sin mantenimiento** — librería con CVE-2024-33663 (algorithm confusion) y CVE-2024-33664 (DoS por JWE) sin parchear; sin releases activos.
2. **`JWT_SECRET` con fallback inseguro** — si la variable no se define, el contenedor arranca con un secret público (`"change-this-secret-in-production"`) y cualquiera puede forjar tokens.
3. **`must_change_password` no se aplica** — la bandera se devuelve al frontend pero el backend no bloquea endpoints; un usuario con credenciales por defecto (`admin/admin`) puede operar la API entera sin cambiar la contraseña.
4. **Sin rate limiting en `/api/auth/login`** — fuerza bruta libre contra el endpoint, agravado por la existencia de credenciales por defecto.
5. **Credenciales OVH en plano en SQLite** — `hosts.password` se guarda como `String` sin cifrar; quien acceda al volumen `data/` se lleva todas las credenciales DynHost.
6. **HTTP requests sin `timeout`** — `requests.get` a OVH y `ipify.get_ip()` no tienen timeout; un upstream colgado bloquea indefinidamente al scheduler (un único hilo).

Este es el momento de cerrarlos: el servicio es de auto-hospedaje y muchos despliegues acabarán expuestos a Internet detrás de un reverse proxy. Cada uno de los seis es bajo coste de cambio y alto retorno de seguridad.

---

## Decisions confirmed with user

| Topic | Decision |
|-------|----------|
| Estrategia de PR | **Un único PR** "security hardening" agrupando los seis riesgos. |
| Clave de cifrado de passwords OVH | **Auto-generada y persistida** en `data/.encryption_key`. Validada en cada arranque (si falta y hay hosts cifrados, fail-fast). |
| Comportamiento si falta `JWT_SECRET` | **Auto-generar y persistir** en `data/.jwt_secret`. Coherente con lo que `CONFIGURATION.md` ya promete ("auto-generated"). |
| Rate limiting | **`slowapi` en memoria** por IP, suficiente para single-instance. |

---

## Design proposal

### 1. Migración a `PyJWT`

Sustituir `python-jose[cryptography]` por `PyJWT`. La superficie de uso en `src/api/auth.py` es mínima (`jwt.encode`, `jwt.decode`, captura de `JWTError`), el mapeo es 1:1 cambiando `jose` por `jwt` y `JWTError` por `jwt.PyJWTError`. HS256 sigue siendo el algoritmo. El `requirements.txt` deja de necesitar `cryptography` directamente (PyJWT lo trae como extra solo si se usan algoritmos asimétricos).

### 2. Gestión de secrets persistidos en `data/`

Nuevo módulo `infrastructure/secrets.py` con dos responsabilidades:

- **`get_or_create_jwt_secret() -> str`**: si `JWT_SECRET` env var existe, la usa; si no, lee `/app/data/.jwt_secret`; si tampoco existe, genera 32 bytes aleatorios (`secrets.token_urlsafe(32)`), los persiste con permisos `0600` y los devuelve.
- **`get_or_create_encryption_key() -> bytes`**: igual para `/app/data/.encryption_key`, generando una clave Fernet (`Fernet.generate_key()`).

`data/` ya está montado como volumen persistente, así que ambos secrets sobreviven a reinicios y reconstrucciones. Permisos `0600` y propiedad del proceso del contenedor.

**Validación en arranque**: si `data/.encryption_key` no existe pero hay filas en `hosts` con valores cifrados (prefijo `enc:v1:`), fallar con error claro en vez de generar una clave nueva que no descifrará nada.

### 3. Cifrado de passwords OVH at-rest

Usar `cryptography.fernet.Fernet` (AES-128-CBC + HMAC-SHA256, autenticado, clave única).

- **Formato persistido**: `enc:v1:<token Fernet base64>`. El prefijo permite detectar plaintext heredado y migrarlo en caliente.
- **Punto de cifrado**: en `SqliteRepository.create_host` y `update_host` (capa de infraestructura). El dominio (`HostConfig.password: SecretStr`) sigue manejando el valor en claro.
- **Punto de descifrado**: en los métodos que materializan `HostConfig` desde la base (`get_hosts`, `get_pending_hosts`, `get_host_by_hostname`).
- **Migración idempotente al arrancar**: nueva función `migrate_plaintext_passwords()` invocada después de `init_db()`. Recorre `hosts`, detecta filas sin prefijo `enc:v1:`, las cifra y reescribe. Solo afecta a despliegues existentes; nuevos arranques no encuentran nada que migrar. Tras esta operación, **nunca** se vuelve a permitir leer plaintext.
- **Sin cambio de schema, cambio de contenido**: el **tipo** de la columna `password` sigue siendo `String` (Fernet emite base64, encaja). Lo que cambia es el **valor almacenado**: ya no plaintext, sino `enc:v1:<ciphertext-base64>`. Tras la migración no queda ninguna password OVH legible en disco.

### 4. Enforcement de `must_change_password`

Refactor de `get_current_user` en `src/api/dependencies.py`:

- Renombrar a **`get_authenticated_user`**: solo verifica el JWT y devuelve el usuario.
- Nueva dependency **`get_current_user`**: usa `get_authenticated_user` y, además, consulta `must_change_password` en la base; si está a `True`, lanza `HTTP 403` con mensaje `"Password change required"`.

`/api/auth/change-password` cambia su dependencia a `get_authenticated_user` (debe ser accesible aunque la contraseña esté pendiente). El resto de routers siguen usando `get_current_user` y quedan bloqueados automáticamente. `/api/auth/login` no lleva dependency.

### 5. Rate limiting con `slowapi`

- Añadir `slowapi` a `requirements.txt`.
- En `src/api/main.py`, crear `Limiter(key_func=get_remote_address)` y registrarlo como middleware + exception handler.
- En `src/api/routers/auth.py`, decorar `login` con `@limiter.limit("5/minute")` y `change_password` con `@limiter.limit("10/minute")`.
- 429 devolverá JSON estándar de slowapi.

Nota: si el servicio queda detrás de un reverse proxy, `get_remote_address` usará la IP del proxy. Documentar en `CONFIGURATION.md` que conviene configurar `X-Forwarded-For` (slowapi soporta `key_func` custom). En este PR no se cubre — issue de seguimiento.

### 6. Timeouts y reemplazo de `ipify-py`

- **OVH client** (`infrastructure/clients/ovh_client.py`): `requests.get(..., timeout=(5, 10))` (connect, read). Mantener tratamiento de `requests.Timeout` dentro del catch existente de `RequestException`.
- **Ipify client** (`infrastructure/clients/ipify_client.py`): la librería `ipify-py` no expone timeout y lleva años sin commits. Sustituir por una llamada directa: `requests.get("https://api.ipify.org", timeout=(5, 10)).text.strip()`. Mismo comportamiento, una dependencia menos. Tests existentes ya mockean a nivel de `IpProvider`, así que el cambio es transparente.
- **Constantes**: definir `OVH_HTTP_TIMEOUT = (5, 10)` e `IPIFY_HTTP_TIMEOUT = (5, 10)` en cada cliente para hacerlas explícitas.

### Secuencia de arranque actualizada

```text
main()
├─ init_db()
├─ migrate_plaintext_passwords()      ← nuevo
├─ get_or_create_jwt_secret()         ← nuevo (lazy en auth.py también)
├─ get_or_create_encryption_key()     ← nuevo
├─ init_admin_user()
└─ ... (resto igual)
```

---

## Scope

### What is included

- Migración `python-jose` → `PyJWT`.
- Persistencia de `JWT_SECRET` y `ENCRYPTION_KEY` en `data/`, auto-generadas si faltan.
- Cifrado at-rest de passwords OVH con migración idempotente del plaintext existente.
- Enforcement real de `must_change_password` en la dependency de auth.
- Rate limiting con `slowapi` en `/api/auth/login` y `/api/auth/change-password`.
- Timeouts en HTTP requests a OVH e ipify, sustituyendo `ipify-py` por `requests`.
- Tests unitarios para todos los caminos nuevos (objetivo ≥90% coverage gate de CI).
- Actualización de `docs/CONFIGURATION.md` para reflejar comportamiento real de `JWT_SECRET` y nueva variable opcional `ENCRYPTION_KEY`.

### What is NOT included

- Rotación de claves (JWT o encryption). Si el usuario borra los ficheros, las passwords cifradas se pierden — documentar.
- Soporte de `X-Forwarded-For` en rate limiting (issue separado).
- Cambio de credenciales por defecto `admin/admin` o forzar contraseña fuerte en cambio (mejora aparte).
- Cifrado de campos distintos a `hosts.password` (hash de usuario, history.details, etc.).
- Headers de seguridad HTTP (CSP, HSTS) — riesgo #11 del audit, no crítico.
- Race condition scheduler vs trigger manual (#7 del audit, fuera de los seis críticos).
- Lockfile de dependencias (`pip-tools`/`uv`) — riesgo #8 del audit.

---

## Affected layers

| Layer | Impact |
|-------|--------|
| API (FastAPI) | `auth.py` (PyJWT, lazy secret), `dependencies.py` (split `get_authenticated_user` / `get_current_user`), `main.py` (registro de slowapi), `routers/auth.py` (decoradores `@limiter.limit`, dependency en change-password). |
| Application | Sin cambios — los ports y el controller no cambian. |
| Domain | Sin cambios. `HostConfig` sigue con `password: SecretStr`. |
| Infrastructure | Nuevo `secrets.py` (gestión de claves persistidas), nuevo `crypto.py` (helper Fernet), `database/repository.py` (cifrar/descifrar en create/update/get_*), nuevo método `migrate_plaintext_passwords` en `database/database.py`, `clients/ovh_client.py` (timeout), `clients/ipify_client.py` (drop `ipify-py`, usar `requests` con timeout). |
| Tests | Nuevos: `test_secrets.py`, `test_crypto.py`, `test_rate_limit.py`, `test_must_change_password.py`. Actualizados: `test_auth.py` (PyJWT, fail-fast paths), `test_repository.py` (cifrado idempotente, migración), `test_ipify_client.py` (sin `ipify-py`), `test_ovh_client.py` (timeout). |
| Docker / CI | `requirements.txt`: `-python-jose`, `-ipify-py`, `+PyJWT`, `+slowapi`, `+cryptography` (explícito si no llega vía PyJWT). Sin cambios en `Dockerfile` ni workflows. |

---

## Implementation order

1. **Dependencias y migración de JWT**: bump `requirements.txt`, refactor `api/auth.py` y `api/dependencies.py` para PyJWT. Tests verdes.
2. **Secrets persistidos**: `infrastructure/secrets.py`, integrar en `auth.py` (lazy `get_jwt_secret`) y en `main.py` (validación temprana de encryption key). Tests del módulo.
3. **Cifrado de passwords OVH**: `infrastructure/crypto.py` (Fernet + prefijo), integrar en `repository.py`, función de migración idempotente, ejecución en `main.py`. Tests de cifrado/descifrado/migración.
4. **Enforcement `must_change_password`**: split de dependencies, ajuste en routers. Test e2e simulando flujo completo.
5. **Rate limiting**: `slowapi` en `main.py` y `routers/auth.py`. Test que verifique 429 tras N intentos.
6. **Timeouts y drop de `ipify-py`**: cambio en ambos clientes, tests con `requests-mock` o equivalente.
7. **Documentación**: actualizar `docs/CONFIGURATION.md`, README si aplica.

Cada paso debe dejar el suite verde antes de continuar (commits granulares dentro del único PR).

---

## Critical files

| File | Changes |
|------|---------|
| `requirements.txt` | -python-jose[cryptography], -ipify-py, +PyJWT~=2.10, +slowapi~=0.1.9, +cryptography~=44.0 |
| `src/api/auth.py` | Importar `jwt` (PyJWT) en vez de `jose`; `decode_token` captura `jwt.PyJWTError`; `get_jwt_secret` delega en `infrastructure.secrets`; eliminar `DEFAULT_JWT_SECRET`. |
| `src/api/dependencies.py` | Renombrar dependency a `get_authenticated_user`; añadir `get_current_user` que comprueba `must_change_password` y lanza 403. |
| `src/api/routers/auth.py` | `change_password` usa `get_authenticated_user`; decorar `login` y `change_password` con `@limiter.limit`. |
| `src/api/main.py` | Registrar `Limiter`, exception handler, middleware. |
| `src/infrastructure/secrets.py` | **Nuevo**: `get_or_create_jwt_secret()`, `get_or_create_encryption_key()`. |
| `src/infrastructure/crypto.py` | **Nuevo**: `encrypt_password(plain)`, `decrypt_password(stored)`, `is_encrypted(value)`. |
| `src/infrastructure/database/database.py` | `migrate_plaintext_passwords()` función idempotente. |
| `src/infrastructure/database/repository.py` | Llamar a `encrypt_password` en `create_host`/`update_host`; `decrypt_password` en `get_hosts`/`get_pending_hosts`/`get_host_by_hostname`. `get_all_hosts`/`get_host_by_id` no devuelven el password (no cambia, sigue oculto). |
| `src/infrastructure/clients/ovh_client.py` | `requests.get(url, auth=auth, timeout=OVH_HTTP_TIMEOUT)`. |
| `src/infrastructure/clients/ipify_client.py` | Reemplazar `ipify.get_ip()` por `requests.get("https://api.ipify.org", timeout=...)`. |
| `src/main.py` | Llamar `migrate_plaintext_passwords()` después de `init_db()`; invocar `get_or_create_encryption_key()` early para fail-fast si DB tiene cifrados y key falta. |
| `src/test/test_auth.py` | Adaptar a PyJWT, eliminar tests del default secret, añadir tests de `get_or_create_jwt_secret`. |
| `src/test/test_secrets.py` | **Nuevo**: cobertura de auto-generación, persistencia, env override. |
| `src/test/test_crypto.py` | **Nuevo**: round-trip, prefijo, detección de plaintext, error si key falta. |
| `src/test/test_repository.py` | Verificar que el password persistido ya no es plaintext y que `get_hosts` lo devuelve descifrado. Test de migración. |
| `src/test/test_rate_limit.py` | **Nuevo**: 6º intento de login devuelve 429. |
| `src/test/test_must_change_password.py` | **Nuevo**: usuario con flag a True solo puede tocar `/change-password`. |
| `docs/CONFIGURATION.md` | Documentar comportamiento auto-generado de `JWT_SECRET`, nueva variable opcional `ENCRYPTION_KEY`, recordatorio de proteger `data/` (contiene secrets). |

---

## Risks and considerations

- **Pérdida de la encryption key**: si el usuario borra `data/.encryption_key` pero conserva la DB, todas las passwords cifradas son irrecuperables. Mitigación: fail-fast claro en arranque (`"Encryption key missing but encrypted hosts found"`) y nota explícita en `CONFIGURATION.md`. No se ofrece recovery.
- **Migración no atómica**: si `migrate_plaintext_passwords()` se interrumpe a mitad (kill -9, OOM), quedará un estado mixto plaintext+cifrado. La función es idempotente y al siguiente arranque continuará. Aceptable: la operación es rápida (un UPDATE por host) y se ejecuta antes de exponer el API.
- **`slowapi` en memoria**: tras reinicio se pierden los contadores. Para un servicio single-instance auto-hospedado es aceptable. Si en el futuro hay multi-instancia, requerirá Redis (issue separado).
- **Compatibilidad PyJWT vs python-jose**: el formato de tokens es estándar JWT, así que tokens emitidos antes del upgrade siguen siendo válidos hasta su expiración (24h). No hay invalidación necesaria.
- **`get_remote_address` con proxy**: documentado como limitación conocida.
- **CI coverage gate (90%)**: los nuevos módulos suman superficie; planificar tests desde el primer paso para no bajar el gate.
- **Tests de auth existentes**: el default secret se elimina, así que `test_get_jwt_secret_default` y `test_get_admin_credentials_defaults` deben adaptarse o desaparecer. No es regresión funcional, es alineamiento con el nuevo contrato.

---

## Open design decisions

Ninguna pendiente. Las cuatro decisiones de diseño abiertas se cerraron antes de redactar este documento. El plan está listo para descomponerse en tasks.
