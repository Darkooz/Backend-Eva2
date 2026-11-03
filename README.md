# Sistema Municipal de Gestión – Ilustre Municipalidad de La Serena

Proyecto Django (Programación Back End, INACAP) – **Evaluación Sumativa N°3: Aplicación web con CRUD**.

Evoluciona el proyecto de las evaluaciones 1 y 2: se elimina el uso de Django Admin y toda la gestión se realiza
desde interfaces propias (Django Templates + Bootstrap local + formularios Django + ORM).

## Funcionalidades

| Requisito de la guía | Implementación |
|---|---|
| Inicio / cierre de sesión | `cuentas` – `LoginView` / `LogoutView` (POST + CSRF) |
| Protección de vistas y restricción por perfil | `LoginRequiredMixin` + `PermissionRequiredMixin` (403 si no tiene permiso) |
| 3 perfiles con permisos diferenciados | Grupos **Administrador**, **Supervisor**, **Administrativo** (`cuentas/permisos.py`) |
| Creación de usuarios y asignación de grupos | Menú *Usuarios* (solo Administrador) |
| Recuperación de contraseña por correo | Solicitud → token seguro (HMAC, 1 uso, vence) → correo con enlace → nueva clave → confirmación |
| Dashboard por perfil | `/cuentas/panel/` redirige al panel del perfil; cada panel valida el perfil |
| 2 mantenedores CRUD | **Delegaciones** y **Autoridades** (crear, listar, buscar, modificar, eliminar, validaciones, paginación) |
| 1 transacción operacional | **Solicitudes ciudadanas**: registro + asignación de autoridad + cambio de estado con historial (`transaction.atomic`) |
| Variables de entorno | `python-decouple` + archivo `.env` (ver `.env.example`) |

### Matriz de permisos

| Operación | Administrador | Supervisor | Administrativo |
|---|:-:|:-:|:-:|
| Ver delegaciones / autoridades | ✅ | ✅ | ✅ |
| Crear / modificar delegaciones y autoridades | ✅ | ✅ | ❌ |
| Eliminar delegaciones y autoridades | ✅ | ❌ | ❌ |
| Ver / registrar solicitudes | ✅ | ✅ | ✅ |
| Asignar autoridad / cambiar estado | ✅ | ✅ | ❌ |
| Eliminar solicitudes | ✅ | ❌ | ❌ |
| Gestión de usuarios y perfiles | ✅ | ❌ | ❌ |

Un superusuario (`createsuperuser`) se comporta como Administrador.

## Estructura

```
config/          settings, urls, utilidades (BootstrapFormMixin, BuscadorMixin, EliminarSeguroMixin)
institucion/     modelos Delegacion y Autoridad + mantenedor de Autoridades + páginas públicas
delegaciones/    mantenedor de Delegaciones + página de contacto
solicitudes/     transacción: Solicitud, SeguimientoSolicitud, services.py (lógica atómica)
cuentas/         login, recuperación de contraseña, dashboards, gestión de usuarios, permisos por perfil
templates/       base.html, crud/ (formulario y confirmación reutilizables), includes/
static/          Bootstrap local (css/js) e imágenes
```

## Instalación local

```bash
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # completar SECRET_KEY y datos de BD
python manage.py migrate                               # crea tablas y los 3 grupos con sus permisos
python manage.py cargar_json                           # carga delegaciones y autoridades iniciales
python manage.py createsuperuser                       # administrador principal
python manage.py crear_usuarios_demo --password 'Clave-Demo-2026!'   # opcional: 1 usuario por perfil
python manage.py runserver
```

Para probar sin MySQL: `DB_ENGINE=django.db.backends.sqlite3` en el `.env`.

## Despliegue en AWS EC2 (Ubuntu)

```bash
git clone URL_DEL_REPOSITORIO && cd Backend-Eva2
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
nano .env                                  # variables (SECRET_KEY, DB_*, EMAIL_*, ALLOWED_HOSTS)
python manage.py migrate
python manage.py cargar_json
python manage.py createsuperuser
python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

Cuando se actualiza el código: `git pull && pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput` y reiniciar gunicorn.

### Correo para recuperar contraseña (producción)

En `.env`:

```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tucuenta@gmail.com
EMAIL_HOST_PASSWORD=contraseña-de-aplicación-de-Gmail
DEFAULT_FROM_EMAIL=tucuenta@gmail.com
```

El enlace del correo usa el host con el que se accedió al sitio (si hay un proxy como Nginx, enviar `proxy_set_header Host $host;`).
Con `EMAIL_BACKEND` por defecto (consola) el correo se imprime en la terminal del servidor.

## Pruebas automáticas

```bash
DB_ENGINE=django.db.backends.sqlite3 python manage.py test
```

40 pruebas cubren login/logout, restricciones por perfil, gestión de usuarios, flujo completo de recuperación de contraseña,
CRUD de ambos mantenedores y la transacción de solicitudes.

IP PUBLICA: *98.87.239.168*
