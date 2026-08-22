# Gym Control — Sistema de Gestión de Gimnasios

**ControlFit Colombia** es un sistema fullstack para la gestión integral de membresías en gimnasios. Permite administrar usuarios, miembros, membresías, pagos, eventos de calendario y notificaciones de forma eficiente, eliminando la necesidad de procesos manuales o hojas de cálculo.

---

## 🚀 Demo Visual

| Módulo | Vista |
|--------|-------|
| **Login** | ![Login](./imgReadme/login.png) |
| **Dashboard** | ![Home](./imgReadme/dashboard.png) |
| **Registro de Miembros** | ![Registro](./imgReadme/resgisterMember.png) |
| **Lista de Miembros** | ![Lista](./imgReadme/listMember.png) |
| **Asignar Membresías** | ![Asignar](./imgReadme/asignarmembresia.png) |
| **Lista de Asignar Membresías** | ![ListaMembresias](./imgReadme/listAsignarMembresia.png) |
| **Perfil de Usuario** | ![Perfil](./imgReadme/perfil.png) |

---

## 🛠️ Tecnologías

### Frontend
| Tecnología | Propósito |
|-------------|-----------|
| React 18 | UI interactiva |
| TypeScript 5.7 | Tipado estático |
| Vite 6 | Build tool rápida |
| Tailwind CSS 4 | Estilos responsivos |
| React Router v7 | Navegación |
| React Hook Form | Formularios |
| Axios | HTTP client con interceptors y auto-refresh |
| react-big-calendar | Calendario de eventos |
| Headless UI | Menú de notificaciones accesible |
| TanStack Table | Tablas del panel de administración |

### Backend
| Tecnología | Propósito |
|-------------|-----------|
| Django 5.2 | Framework Python |
| Django Rest Framework | API REST |
| SimpleJWT | Autenticación JWT con rotación y blacklist |
| PostgreSQL / MySql | Base de datos |
| CORS Headers | Cross-origin config con credenciales |
| django-storages + boto3 | Avatares en storage compatible S3 (Supabase) |

---

## 🔐 Sistema de Autenticación (JWT + cookie HttpOnly)

El proyecto implementa autenticación **JWT** pensada para producción: el *access token* vive en el frontend y el *refresh token* nunca toca JavaScript — viaja únicamente en una cookie **HttpOnly**, lo que lo protege contra ataques XSS.

### Flujo de Autenticación

```
LOGIN
─────
Frontend ── POST /gym/api/v1/token/ {email, password} ──► Backend (Django)
         ◄── 200 {access} + Set-Cookie: refresh_token ──
             (HttpOnly · Path=/gym/api/v1/ · 7 días)

REQUEST AUTORIZADA
──────────────────
Frontend ── GET /gym/api/v1/me/ ─────────────────────────► Backend
            Header: Authorization: Bearer {access}

AUTO-REFRESH (proactivo + reactivo)
───────────────────────────────────
• Proactivo: refresh silencioso cada 20 min y cuando al access
  le quedan menos de 5 min de vida
• Reactivo:  interceptor axios ante un 401
             → POST /gym/api/v1/token/refresh/ (la cookie viaja sola)
             → nuevo access → se reintenta la request original

LOGOUT
──────
Frontend ── POST /gym/api/v1/auth/logout/ ───────────────► Backend
                                                          Blacklist del refresh
                                                          + eliminación de cookie
Frontend limpia el access (sessionStorage) e isAuthenticated = false
```

### Endpoints de Autenticación

| Método | Endpoint | Descripción |
|--------|----------|------------|
| POST | `/gym/api/v1/token/` | Login (retorna `access`; el `refresh` va en cookie) |
| POST | `/gym/api/v1/token/refresh/` | Renueva el access token (lee y rota la cookie) |
| POST | `/gym/api/v1/auth/logout/` | Logout: blacklist del refresh + borra cookie |
| POST | `/gym/api/v1/register/` | Registro público (auto-crea gimnasio) |
| GET | `/gym/api/v1/me/` | Perfil del usuario autenticado |

### Seguridad

| Característica | Implementación |
|----------------|---------------|
| Access Token | `sessionStorage` (`gym_access_token`) — sobrevive recargas, no usa localStorage |
| Refresh Token | Cookie `refresh_token` HttpOnly — inaccesible desde JavaScript (anti-XSS) |
| Ámbito de cookie | `Path=/gym/api/v1/` — solo se envía a los endpoints de la API |
| SameSite / Secure | Dev: `Lax` · Producción: `None` + `Secure` (cross-site Vercel → Render) |
| Rotación | Cada refresh emite un nuevo refresh token y blacklistea el anterior |
| Logout | Blacklist del refresh + borrado de cookie (idempotente) |
| Auto-refresh | Interceptor axios 401 → refresh → retry, más refresh proactivo |
| Credenciales | Ambos clientes axios usan `withCredentials: true` |

---

## ✨ Características

- **Gestión de Miembros**: Registro, edición, eliminación y visualización
- **Control de Membresías**: Seguimiento de estados de pago y vencimiento
- **Multi-tenant**: Cada usuario tiene su propio gimnasio (middleware + mixins)
- **Registro Público**: Usuarios nuevos pueden registrarse sin admin
- **📅 Calendario de Eventos**: CRUD de eventos y tipos, drag & drop y vista pública
- **🔔 Notificaciones Automáticas**: Membresías por vencer/vencidas y eventos del día, con deep links y WhatsApp
- **📝 Solicitudes de Demo**: Embudo de prospectos con panel exclusivo para superadmin
- **Exportación**: Reportes en Excel
- **Interfaz Responsiva**: Optimizado para tablets y escritorio

---

## 🧩 Módulos Destacados

### 📅 Calendario de Eventos

- CRUD completo de **eventos** y **tipos de evento** (la gestión de tipos vive dentro de la página del calendario)
- Reprogramación por **drag & drop** (guarda con `PATCH`)
- Consulta por rango de fechas (`?start=&end=`)
- **Calendario público** de solo lectura por gimnasio para integraciones externas

### 🔔 Notificaciones

- **Generación perezosa e idempotente**: se calculan al consultar la API (sin cron ni Celery); una constraint en BD garantiza una única notificación por gimnasio/tipo/relación
- Tipos: `por_vencer` (membresías que vencen en ≤ 3 días), `vencida` y `evento` (eventos de hoy)
- La lista devuelve solo **no leídas**; contador para el badge y marcado individual o masivo
- **Deep link**: una notificación de evento abre directamente su modal en `/dashboard/calendar?evento={id}`
- Botón de **contacto rápido por WhatsApp** (`wa.me`) por notificación
- Campanita en el header con polling cada 5 minutos

### 📝 Solicitudes de Demo

- Formulario público en `/solicitar-demo` donde prospectos dejan nombre, email, teléfono y nombre del gimnasio
- Estados gestionables: `pendiente` → `contactado`
- Panel de gestión en `/platform/solicitudes-demo`, protegido por `SuperAdminRoute` (rol `superadmin`)
- ⚠️ La restricción `superadmin` se aplica a nivel de frontend; en el backend la consulta/gestión requiere solo autenticación

---

## ⚙️ Configuración e Instalación

### 1. Clonar el repositorio

```bash
git clone <url_del_repositorio>
cd ControlFit
```

### 2. Backend (Django)

#### Crear entorno virtual

```bash
python -m venv venv
```

#### Activar entorno virtual

```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

#### Instalar dependencias

```bash
pip install -r requirements.txt
```

#### Configurar variables de entorno

```bash
# Copiar .env.example a .env y configurar
cp .env.example .env
```

#### Ejecutar migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

#### Crear superusuario (opcional)

```bash
python manage.py createsuperuser
```

#### Iniciar servidor

```bash
python manage.py runserver
# Servidor disponible en http://localhost:8000
```

### 3. Frontend (React + Vite)

#### Instalar dependencias

```bash
cd gimnasioReact
npm install
```

#### Configurar variables de entorno

```bash
# Verificar .env tiene las URLs correctas
VITE_API_URL_DEV=http://localhost:8000/gym/api/v1
```

#### Iniciar desarrollo

```bash
npm run dev
# App disponible en http://localhost:5173
```

#### Build para producción

```bash
npm run build
```

---

## 📁 Estructura del Proyecto

```
ControlFit/
├── gimnasio/                       # Proyecto Django
│   ├── settings.py                 # Configuración principal
│   └── urls.py                     # Rutas principales
├── gimnasioApp/                    # App principal Django
│   ├── models.py                   # Usuario, UserGym, Membresías, Eventos, Notification, DemoRequest
│   ├── views.py                    # ViewSets + vistas de auth con cookie
│   ├── serializers.py              # Serializadores DRF
│   ├── urls.py                     # Rutas API
│   ├── auth_cookie.py              # Helpers de cookie refresh token
│   ├── middleware.py               # Multi-tenant (request.gimnasio)
│   ├── mixins.py / permissions.py  # MultiTenantViewSetMixin y roles
│   ├── services/
│   │   └── notifications.py        # Generador idempotente de notificaciones
│   └── storage.py                  # Storage S3 (Supabase) para avatares
├── gimnasioReact/                  # Frontend React + Vite
│   └── src/
│       ├── api/
│       │   ├── axios/              # axios.public.ts, axios.private.ts, refreshToken.api.ts
│       │   ├── action/             # Clients por módulo (calendario, notifications, demoRequests…)
│       │   └── users/              # API calls de usuarios
│       ├── components/
│       │   └── headerNav/          # NotificationMenu y navegación
│       ├── context/                # AuthContext
│       ├── layouts/                # Layouts
│       ├── model/                  # DTOs TypeScript (dto/, calendario.model.ts, notifications.model.ts)
│       ├── pages/
│       │   ├── auth/               # Login, Register, SolicitarDemoPage…
│       │   └── admin/              # Dashboard, demo/, notifications/, calendario/
│       ├── routes/
│       │   └── protectedRoute/     # ProtectedRoute, SuperAdminRoute
│       ├── utils/
│       │   └── authStorage.ts      # Access token (sessionStorage)
│       ├── App.tsx
│       └── main.tsx
├── .env.example
├── requirements.txt
└── README.md
```

### Estructura Frontend Detallada

| Carpeta | Contenido |
|---------|-----------|
| `src/api/axios/` | Instancias axios (pública/privada) y lógica de refresh |
| `src/api/action/` | Clients API por módulo (calendario, notificaciones, demos…) |
| `src/model/` | Interfaces TypeScript (DTOs y modelos de dominio) |
| `src/context/` | AuthContext y Provider |
| `src/pages/auth/` | Login, Register, SolicitarDemo |
| `src/pages/admin/` | Dashboard, miembros, membresías, calendario, notificaciones, demos |
| `src/routes/protectedRoute/` | Rutas protegidas y guard de superadmin |
| `src/utils/` | authStorage, helpers de fechas |

---

## 🔧 Variables de Entorno

### Backend (.env)

```env
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=postgres://user:password@localhost:5432/gimnasio
ALLOWED_HOSTS=localhost,127.0.0.1

# Datos semilla del entorno demo (opcional)
DEMO_ADMIN_EMAIL=
DEMO_ADMIN_PASSWORD=
DEMO_ADMIN_NAME=
DEMO_ADMIN_LASTNAME=

# Número para enlaces de WhatsApp (opcional)
WHATSAPP_NUMBER=

# Storage S3 (Supabase) para avatares — producción
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

## 🧪 API Endpoints

Base URL: `/gym/api/v1/`

### Autenticación

| Método | Endpoint | Público | Descripción |
|--------|----------|---------|-------------|
| POST | `/token/` | ✅ | Login (retorna `access`; el `refresh` va en cookie) |
| POST | `/token/refresh/` | ✅ | Refresh token (rota la cookie) |
| POST | `/auth/logout/` | ❌ | Logout: blacklist + borra cookie |
| POST | `/register/` | ✅ | Registro nuevo (crea usuario + gimnasio) |
| GET | `/me/` | ❌ | Perfil actual |

### Usuarios

| Método | Endpoint | Público | Descripción |
|--------|----------|---------|-------------|
| GET | `/me/` | ❌ | Perfil actual |
| GET | `/User/` | ❌ | Listar usuarios |
| POST | `/User/` | ❌ | Crear usuario |
| GET | `/User/{id}/` | ❌ | Ver usuario |
| PUT | `/User/{id}/` | ❌ | Actualizar usuario |
| DELETE | `/User/{id}/` | ❌ | Eliminar usuario |

### Miembros

| Método | Endpoint | Público | Descripción |
|--------|----------|---------|-------------|
| GET | `/UserGym/` | ❌ | Lista miembros |
| POST | `/UserGym/` | ❌ | Registrar miembro |
| GET | `/UserGymDay/` | ❌ | Miembros por día |

### Membresías

| Método | Endpoint | Público | Descripción |
|--------|----------|---------|-------------|
| GET | `/MemberShips/` | ❌ | Lista membresías |
| POST | `/MemberShips/` | ❌ | Crear membresía |
| GET | `/MemberShipsAsignada/` | ❌ | Membresías asignadas |
| POST | `/MemberShipsAsignada/` | ❌ | Asignar membresía |

### Calendario

| Método | Endpoint | Público | Descripción |
|--------|----------|---------|-------------|
| GET/POST | `/TiposEvento/` | ❌ | Tipos de evento (solo admin) |
| GET/POST | `/CalendarioEventos/` | ❌ | Eventos (soporta `?start=&end=`) |
| PATCH | `/CalendarioEventos/{id}/` | ❌ | Editar / reprogramar (drag & drop) |
| GET | `/api/calendario/publico/{gimnasio_id}/` | ✅ | Calendario público del gimnasio |

### Notificaciones

| Método | Endpoint | Público | Descripción |
|--------|----------|---------|-------------|
| GET | `/Notificaciones/` | ❌ | No leídas (genera pendientes al consultar) |
| GET | `/Notificaciones/no-leidas/` | ❌ | Contador para el badge |
| POST | `/Notificaciones/{id}/marcar-leida/` | ❌ | Marcar una como leída |
| POST | `/Notificaciones/marcar-todas-leidas/` | ❌ | Marcar todas como leídas |

### Solicitudes de Demo

| Método | Endpoint | Público | Descripción |
|--------|----------|---------|-------------|
| POST | `/solicitudes-demo/` | ✅ | Enviar solicitud (formulario público) |
| GET | `/solicitudes-demo/` | ❌ | Listar solicitudes (panel superadmin) |
| PATCH | `/solicitudes-demo/{id}/` | ❌ | Cambiar estado (`pendiente` → `contactado`) |

---

## 📄 Licencia

MIT License — Libre para usar y modificar.

---

## 👤 Autor

Oscar Eduardo Lozano Bocanegra — [GitHub](https://github.com/Olozano1194)