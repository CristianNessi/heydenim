# Heydemin — Tienda Online de Denim Femenino

Aplicación web completa para la tienda **Heydemin**, una marca de denim femenino premium. Incluye landing page pública, panel de administración, integración de pagos con SumUp y analíticas propias.

---

## Tecnologías utilizadas

| Capa | Tecnología |
|---|---|
| Backend | Python 3.11+ · FastAPI · Uvicorn |
| ORM / DB | SQLAlchemy 2.x · PostgreSQL |
| Templates | Jinja2 |
| Autenticación | bcrypt · Starlette Sessions |
| Pagos | SumUp Hosted Checkout API |
| Frontend | HTML5 · CSS3 · JavaScript (Vanilla) |
| Fuentes | Google Fonts (Inter, Playfair Display) |
| Iconos | Font Awesome 6.5 |
| Gráficos | Chart.js 4.4 |
| Variables de entorno | python-dotenv |
| HTTP client | httpx |
| Cifrado (vault) | cryptography (Fernet + PBKDF2-SHA256) |

---

## Estructura del proyecto

```
heydemin/
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── admin.py          # Panel admin (login, productos, contenido)
│   │       ├── analytics.py      # Métricas, notificaciones
│   │       ├── cart.py           # Carrito de compras
│   │       ├── checkout.py       # Proceso de pago con SumUp
│   │       ├── products.py       # API pública de productos
│   │       └── seo.py            # Sitemap, robots.txt
│   ├── core/
│   │   └── config.py             # Configuración y variables de entorno
│   ├── db/
│   │   ├── database.py           # Engine, sesión y migraciones automáticas
│   │   └── models/
│   │       ├── admin_user.py     # Usuarios admin (multi-usuario)
│   │       ├── analytics.py      # PageView, ClickEvent
│   │       ├── notification.py   # Notificaciones del panel
│   │       ├── product.py        # Product
│   │       ├── sale.py           # Sale
│   │       └── site_content.py   # Contenido editable del landing
│   ├── services/
│   │   ├── notifications.py      # Helpers para crear notificaciones
│   │   └── sumup.py              # Cliente SumUp Hosted Checkout
│   ├── static/
│   │   ├── css/
│   │   │   ├── styles.css        # Estilos tienda pública
│   │   │   └── admin.css         # Estilos panel admin
│   │   ├── imagen/               # Logo y favicon
│   │   ├── js/
│   │   │   ├── app.js            # Lógica tienda pública
│   │   │   └── admin-dashboard.js
│   │   └── uploads/              # Imágenes subidas por el admin
│   ├── templates/
│   │   ├── index.html            # Landing page pública
│   │   └── admin/
│   │       ├── login.html
│   │       ├── dashboard.html
│   │       ├── products.html
│   │       ├── product_form.html
│   │       ├── content.html
│   │       └── notifications.html
│   └── main.py
├── scripts/
│   ├── manage_admins.py          # Gestión de usuarios admin (ver más abajo)
│   ├── vault.py                  # Notas privadas encriptadas (ver más abajo)
│   └── checkout_test.py          # Prueba de checkout SumUp
├── create_tables.py
├── test_db.py
├── run.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## Requisitos previos

- Python 3.11 o superior
- PostgreSQL (local o en la nube)
- Cuenta SumUp con API Key y Hosted Checkout habilitado

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/heydemin.git
cd heydemin
```

### 2. Crear y activar el entorno virtual

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
cp .env.example .env
```

Completar `.env` con los valores reales (ver `.env.example` como referencia).

### 5. Crear las tablas e iniciar

```bash
python run.py
```

Las tablas se crean automáticamente al arrancar. El usuario admin del `.env` se migra a la tabla `admin_users` en el primer inicio.

---

## Variables de entorno (`.env`)

| Variable | Descripción |
|---|---|
| `DATABASE_URL` | URL de conexión PostgreSQL |
| `SUMUP_API_KEY` | API Key de SumUp (`sup_sk_...`) |
| `SUMUP_MERCHANT_CODE` | Código de comerciante SumUp |
| `SUMUP_PAY_TO_EMAIL` | Email de la cuenta SumUp |
| `SUMUP_REDIRECT_URL` | URL a donde va el usuario tras pagar |
| `ADMIN_EMAIL` | Email del admin inicial (se migra a DB) |
| `ADMIN_PASSWORD_HASH` | Hash bcrypt de la contraseña admin |
| `SESSION_SECRET` | Clave secreta para sesiones (mín. 32 chars) |

Para generar `ADMIN_PASSWORD_HASH`:

```bash
python -c "import bcrypt; print(bcrypt.hashpw(b'tu_password', bcrypt.gensalt()).decode())"
```

Para generar `SESSION_SECRET`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Gestión de usuarios admin

El sistema soporta múltiples usuarios admin. Se gestionan con el script `scripts/manage_admins.py`.

```bash
# Ver todos los usuarios
python scripts/manage_admins.py list

# Agregar un usuario nuevo
python scripts/manage_admins.py add email@ejemplo.com contraseña

# Eliminar un usuario (pide confirmación)
python scripts/manage_admins.py delete email@ejemplo.com

# Desactivar sin borrar (no puede loguearse)
python scripts/manage_admins.py disable email@ejemplo.com

# Reactivar
python scripts/manage_admins.py enable email@ejemplo.com

# Cambiar contraseña
python scripts/manage_admins.py password email@ejemplo.com nueva_contraseña
```

> Las credenciales reales (emails, contraseñas) no van en este README. Usá el vault (ver abajo).

---

## Vault — Notas privadas encriptadas

Para guardar credenciales, contraseñas y notas sensibles de forma segura existe el vault: un archivo `.vault` encriptado con AES-256 (Fernet + PBKDF2-SHA256) que solo se puede abrir con tu contraseña maestra.

```bash
# Crear el vault por primera vez
python scripts/vault.py init

# Leer el contenido
python scripts/vault.py read

# Editar (abre el editor de texto configurado)
python scripts/vault.py edit

# Cambiar la contraseña maestra
python scripts/vault.py change-pass
```

El archivo `.vault` está en `.gitignore` y nunca se sube al repositorio.

---

## Rutas principales

### Tienda pública

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Landing page |
| GET | `/api/products` | Lista de productos |
| GET | `/api/products/{id}` | Detalle de producto |
| POST | `/checkout/` | Iniciar pago con SumUp |
| GET | `/checkout/thank-you` | Página de confirmación post-pago |
| GET | `/sitemap.xml` | Sitemap SEO |
| GET | `/robots.txt` | Robots SEO |

### Panel de administración

| Método | Ruta | Descripción |
|---|---|---|
| GET/POST | `/admin/login` | Login admin |
| GET | `/admin/logout` | Cerrar sesión |
| GET | `/admin/dashboard` | Dashboard con métricas |
| GET | `/admin/products` | Listado de productos |
| GET/POST | `/admin/products/new` | Crear producto |
| GET/POST | `/admin/products/edit/{id}` | Editar producto |
| POST | `/admin/products/delete/{id}` | Eliminar producto |
| GET | `/admin/content` | Editor de contenido del landing |
| GET | `/admin/notifications` | Centro de notificaciones |

### Analíticas y notificaciones

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/analytics/pageview` | Registrar visita |
| POST | `/analytics/click` | Registrar clic |
| GET | `/analytics/metrics` | Métricas (admin) |
| GET | `/analytics/notifications` | Listar notificaciones |
| POST | `/analytics/notifications/read-all` | Marcar todas como leídas |
| POST | `/analytics/notifications/{id}/read` | Marcar una como leída |
| DELETE | `/analytics/notifications/{id}` | Eliminar notificación |

---

## Integración SumUp

El flujo de pago usa **Hosted Checkout**:

1. El frontend envía el carrito a `POST /checkout/`
2. El backend crea un checkout en la API de SumUp con `hosted_checkout: {enabled: true}`
3. SumUp devuelve una `hosted_checkout_url`
4. El usuario es redirigido a la página de pago de SumUp
5. Tras el pago, SumUp redirige a `SUMUP_REDIRECT_URL` (configurado en `.env`)

Requisitos en el dashboard de SumUp:
- Hosted Checkout habilitado para el merchant
- `SUMUP_REDIRECT_URL` debe apuntar a la URL de producción (`https://heydemin.com/checkout/thank-you`)

---

## Despliegue en producción

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

Checklist antes de subir:
- [ ] `SESSION_SECRET` con valor aleatorio seguro (mín. 32 chars)
- [ ] `SUMUP_REDIRECT_URL` apuntando al dominio real (no localhost)
- [ ] `secure=True` en la cookie de sesión (requiere HTTPS) — en `app/api/routes/admin.py`
- [ ] PostgreSQL en la nube (Railway, Supabase, Neon, etc.)
- [ ] HTTPS configurado (Nginx + Certbot o Caddy)
- [ ] `.env` y `.vault` fuera del repositorio

---

## TODO

- [ ] Recuperación de contraseña por email
- [ ] Paginación en el catálogo público
- [ ] Filtros por talle y precio
- [ ] Notificaciones por email al completar una venta
- [ ] Exportar ventas a CSV
- [ ] Tests automatizados (pytest)
- [ ] Docker / docker-compose

---

## Licencia

Proyecto privado — todos los derechos reservados © Heydemin.
