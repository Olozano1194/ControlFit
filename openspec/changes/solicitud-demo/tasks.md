# Tasks: solicitud-demo

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~150 |
| 400-line budget risk | Low |
| Delivery strategy | single-pr |

### Suggested Work Units

| Unit | Goal |
|------|------|
| 1 | Backend: Modelo `DemoRequest`, Serializer y ViewSet público (`/solicitudes-demo/`). |
| 2 | Frontend: Pantalla `SolicitarDemoPage.tsx` y enrutamiento desde `LoginPage.tsx`. |

## Phase 1: Backend — Modelo y API

- [x] 1.1 Crear modelo `DemoRequest` en `gimnasioApp/models.py` (nombre, email, telefono, gimnasio, estado, fecha).
- [x] 1.2 Crear `DemoRequestSerializer` en `gimnasioApp/serializers.py`.
- [x] 1.3 Crear `DemoRequestViewSet` en `gimnasioApp/views.py` con `AllowAny` y métodos limitados a POST.
- [x] 1.4 Registrar la ruta `solicitudes-demo` en `gimnasioApp/urls.py`.
- [x] 1.5 Correr migraciones y aplicarlas.

## Phase 2: Frontend — Pantalla y Enrutamiento

- [x] 2.1 Crear archivo `gimnasioReact/src/pages/auth/SolicitarDemoPage.tsx` con formulario usando `react-hook-form`.
- [x] 2.2 Configurar petición POST a `/solicitudes-demo/` usando `axiosPublic`.
- [x] 2.3 Manejar estado de carga (`isSubmitting`) y mensaje de éxito (UI de confirmación).
- [x] 2.4 Agregar ruta `/solicitar-demo` en `gimnasioReact/src/App.tsx`.
- [x] 2.5 Modificar el botón "Solicitar una Demo" en `LoginPage.tsx` para que use `navigate('/solicitar-demo')` en lugar de una alerta.

## Status
Toda la funcionalidad fue implementada y conectada con éxito.
