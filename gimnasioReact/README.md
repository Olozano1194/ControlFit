# ControlFit — Frontend (React + TypeScript + Vite)

SPA del sistema de gestión de gimnasios ControlFit. Consume la API Django/DRF del backend (carpetas `../gimnasio/` y `../gimnasioApp/`). Para el panorama completo del proyecto, ver el [`README` raíz](../README.md).

## Requisitos

- Node.js 20+
- Backend corriendo localmente (ver [`../README.md`](../README.md))

## Puesta en marcha

```bash
npm install
npm run dev        # http://localhost:5173
```

Depende del backend en `http://localhost:8000`. El endpoint se configura en `.env`:

```env
VITE_API_URL_DEV=http://localhost:8000/gym/api/v1
VITE_API_URL_PROD=https://tu-dominio.render.com/gym/api/v1
```

## Scripts

| Script | Acción |
|--------|--------|
| `npm run dev` | Servidor de desarrollo (Vite + HMR) |
| `npm run build` | Typecheck (`tsc -b`) + build de producción |
| `npm run preview` | Sirve el build generado localmente |
| `npm run lint` | ESLint (incluye la regla `max-lines: 250`) |
| `npm test` | Suite completa (Vitest) |
| `npm run test:watch` | Vitest en modo watch |

## Gate antes de cerrar un cambio

Obligatorio antes de dar por terminado un cambio:

```bash
npx tsc -b        # typecheck
npm run lint      # ESLint
npm test          # Vitest
```

## Estructura

| Ruta | Contenido |
|------|-----------|
| `src/api/axios/` | Instancias axios + lógica de refresh del token |
| `src/api/action/` | Clients de API por módulo |
| `src/model/` | DTOs / modelos TypeScript |
| `src/context/` | AuthContext |
| `src/components/` | Componentes reutilizables (ui, formularios, tablas) |
| `src/pages/auth/` | Login, Register, SolicitarDemo |
| `src/pages/admin/` | Dashboard, miembros, membresías, calendario, notificaciones, demos |
| `src/routes/protectedRoute/` | ProtectedRoute, SuperAdminRoute |
| `src/utils/` | Helpers: `authStorage.ts`, `apiError.ts`, `dateUtils.ts`, ... |

## Convenciones

- **Máximo 250 líneas por archivo**, sin excepciones para archivos nuevos.
- **Commits en Conventional Commits con descripción en español**, sin atribución a IA.

Detalle completo y cómo se hace cumplir en [`../AGENTS.md`](../AGENTS.md).
