# ControlFit — Sistema de Gestión de Gimnasios

Sistema fullstack para gestión integral de membresías en gimnasios: usuarios, miembros, membresías, pagos, calendario de eventos, notificaciones automáticas y solicitudes de demo. Elimina procesos manuales y hojas de cálculo.

---

## 🚀 Demo Visual

| Módulo | Vista |
|--------|-------|
| **Login** | ![Login](./imgReadme/login.png) |
| **Dashboard** | ![Home](./imgReadme/dashboard.png) |
| **Registro de Miembros** | ![Registro](./imgReadme/resgisterMember.png) |
| **Lista de Miembros** | ![Lista](./imgReadme/listMember.png) |
| **Asignar Membresías** | ![Asignar](./imgReadme/asignarmembresia.png) |
| **Lista de Membresías** | ![ListaMembresias](./imgReadme/listAsignarMembresia.png) |
| **Perfil de Usuario** | ![Perfil](./imgReadme/perfil.png) |

---

## 🛠️ Tecnologías

### Frontend
React 18, TypeScript 5.7, Vite 6, Tailwind CSS 4, React Router v7, React Hook Form, Axios (interceptors + auto-refresh), react-big-calendar, Headless UI, TanStack Table.

### Backend
Django 5.2, Django REST Framework, SimpleJWT (rotación + blacklist), PostgreSQL, CORS Headers, django-storages + boto3 (avatares en Supabase S3).

---

## 🔐 Autenticación JWT + Cookie HttpOnly

- **Access token**: `sessionStorage` (`gym_access_token`), sobrevive recargas.
- **Refresh token**: Cookie `refresh_token` **HttpOnly** (Path `/gym/api/v1/`), inaccesible desde JS → anti-XSS.
- **Rotación**: cada refresh emite nuevo refresh y blacklistea el anterior.
- **Auto-refresh**: proactivo (cada 20 min / < 5 min de vida) + reactivo (interceptor axios ante 401 → refresh → retry).
- **Logout**: blacklist del refresh + borrado de cookie (idempotente).

### Endpoints Auth
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/gym/api/v1/token/` | Login (retorna `access`; `refresh` en cookie) |
| POST | `/gym/api/v1/token/refresh/` | Renueva access (rota cookie) |
| POST | `/gym/api/v1/auth/logout/` | Logout: blacklist + borra cookie |
| POST | `/gym/api/v1/register/` | Registro público (auto-crea gimnasio) |
| GET | `/gym/api/v1/me/` | Perfil autenticado |

---

## ✨ Características Principales

- **Gestión de Miembros**: CRUD completo con estados.
- **Control de Membresías**: Seguimiento de pagos y vencimientos.
- **Multi-tenant**: Cada usuario pertenece a un gimnasio (middleware `request.gimnasio` + `MultiTenantViewSetMixin`).
- **Registro Público**: Usuarios nuevos se registran sin admin → auto-crea su gimnasio.
- **Calendario de Eventos**: CRUD eventos/tipos, drag & drop, vista pública por gimnasio.
- **Notificaciones Automáticas**: Generación perezosa e idempotente (sin cron/Celery), tipos: `por_vencer`, `vencida`, `evento`. Deep links + WhatsApp. Badge con polling 5 min.
- **Solicitudes de Demo**: Formulario público `/solicitar-demo`, panel gestión `/platform/solicitudes-demo` (protegido por rol `superadmin`).
- **Exportación**: Reportes en Excel.
- **Responsive**: Optimizado tablet/escritorio.

---

## 🧩 Módulos Destacados

### 📅 Calendario
- CRUD eventos y tipos (tipos gestionados dentro de la página del calendario).
- Reprogramación drag & drop (`PATCH`).
- Consulta por rango (`?start=&end=`).
- Calendario público de solo lectura por gimnasio.

### 🔔 Notificaciones
- Generación **perezosa e idempotente** al consultar la API (constraint BD evita duplicados).
- Tipos: `por_vencer` (≤3 días), `vencida`, `evento` (hoy).
- Solo no leídas en lista; contador para badge; marcado individual/masivo.
- Deep link: `/dashboard/calendar?evento={id}` abre modal del evento.
- Botón WhatsApp (`wa.me`) por notificación.

### 📝 Solicitudes de Demo
- Formulario público: nombre, email, teléfono, nombre gimnasio.
- Estados: `pendiente` → `contactado`.
- Panel en `/platform/solicitudes-demo` (requiere rol `superadmin`).

---

## ⚙️ Instalación Local

### 1. Backend (Django)
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env  # Configurar variables
python manage.py migrate
python manage.py runserver  # http://localhost:8000
```

### 2. Frontend (React + Vite)
```bash
cd gimnasioReact
npm install
# Verificar .env: VITE_API_URL_DEV=http://localhost:8000/gym/api/v1
npm run dev  # http://localhost:5173
```

---

## 📁 Estructura del Proyecto

```
ControlFit/
├── gimnasio/                 # Configuración Django (settings, urls, wsgi)
├── gimnasioApp/              # App principal
│   ├── models.py             # Usuario, UserGym, Membresías, Eventos, Notification, DemoRequest
│   ├── views.py              # ViewSets + auth con cookie
│   ├── serializers.py
│   ├── urls.py
│   ├── auth_cookie.py        # Helpers cookie refresh
│   ├── middleware.py         # Multi-tenant (request.gimnasio)
│   ├── mixins.py             # MultiTenantViewSetMixin, permisos por rol
│   ├── services/notifications.py  # Generador idempotente
│   └── storage.py            # Storage S3 (Supabase) avatares
├── gimnasioReact/            # Frontend React + Vite
│   └── src/
│       ├── api/axios/        # Instancias axios + refresh logic
│       ├── api/action/       # Clients por módulo
│       ├── model/            # DTOs TypeScript
│       ├── context/          # AuthContext
│       ├── pages/auth/       # Login, Register, SolicitarDemo
│       ├── pages/admin/      # Dashboard, miembros, membresías, calendario, notificaciones, demos
│       ├── routes/protectedRoute/  # ProtectedRoute, SuperAdminRoute
│       └── utils/authStorage.ts    # Access token (sessionStorage)
├── .env.example
├── requirements.txt
├── build.sh                  # Render build phase
├── start.sh                  # Render start phase (entrypoint)
└── README.md
```

---

## 🔧 Variables de Entorno

### Backend (.env)
```env
SECRET_KEY=...
DEBUG=True
DATABASE_URL=postgres://user:pass@localhost:5432/gimnasio
ALLOWED_HOSTS=localhost,127.0.0.1

# Demo Admin (auto-creado en apps.py, TIENE gimnasio asignado)
DEMO_ADMIN_EMAIL=reclutador@gimnasio.com
DEMO_ADMIN_PASSWORD=Gimnasio2026!
DEMO_ADMIN_NAME=Recruiter
DEMO_ADMIN_LASTNAME=Demo

# Superadmin Plataforma (global, SIN gimnasio) — crea con: python manage.py create_superadmin
SUPERADMIN_EMAIL=tu-email@ejemplo.com
SUPERADMIN_PASSWORD=TuPasswordSuperSegura123!
SUPERADMIN_NAME=Super
SUPERADMIN_LASTNAME=Admin

# Admin Gimnasio (producción, CON gimnasio) — crea con: python manage.py create_production_admin
ADMIN_EMAIL=admin@tugimnasio.com
ADMIN_PASSWORD=TuPasswordGym123!
ADMIN_NAME=Admin
ADMIN_LASTNAME=Gimnasio
ADMIN_GIMNASIO_NAME=Mi Gimnasio
ADMIN_GIMNASIO_ADDRESS=Dirección del gimnasio
ADMIN_GIMNASIO_PHONE=3001234567

WHATSAPP_NUMBER=

# S3 (Supabase) — producción
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
AWS_S3_ENDPOINT_URL=
AWS_S3_REGION_NAME=
```

### Frontend (.env)
```env
VITE_API_URL_DEV=http://localhost:8000/gym/api/v1
VITE_API_URL_PROD=https://tu-dominio.render.com/gym/api/v1
```

---

## 🚢 Despliegue en Render

1. **Build Command**: `./build.sh` (instala deps, collectstatic, migra)
2. **Start Command**: `./start.sh` (migra, crea superadmin/admin, collectstatic, **inicia Gunicorn**)
3. Configurar variables de entorno en Render (Settings → Environment) con los valores de producción.

`start.sh` es **idempotente**: si los usuarios ya existen, no falla ni duplica.

---

## 📄 Licencia

MIT — Libre para usar y modificar.

---

## 👤 Autor

Oscar Eduardo Lozano Bocanegra — [GitHub](https://github.com/Olozano1194)