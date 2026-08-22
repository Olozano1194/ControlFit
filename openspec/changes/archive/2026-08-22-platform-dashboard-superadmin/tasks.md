# Tasks: Platform Dashboard for SuperAdmin

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 500-650 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 → PR 2 → PR 3 |
| Delivery strategy | ask-on-risk |
| Chain strategy | stacked-to-main |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Backend foundation + platform API | PR 1 | `pytest -k platform` | Django test client | `gimnasioApp/` changes (permissions, serializers, views, urls, tests) |
| 2 | Frontend foundation + DTOs + API client + layout | PR 2 | `npm test -- platform` | Vitest + jsdom | `gimnasioReact/src/` infrastructure files (DTOs, API, layout, sidebar) |
| 3 | Frontend pages + routes + integration | PR 3 | `npm test -- platform` + manual | Vitest + browser | `gimnasioReact/src/pages/`, `App.tsx` routes |

## Phase 1: Backend Foundation

- [x] 1.1 Add `IsSuperAdmin` permission class to `gimnasioApp/permissions.py` — checks `request.user.roles == 'superadmin'` combined with `IsAuthenticated`
- [x] 1.2 Add `PlatformPagination` class to `gimnasio/settings.py` — `PageNumberPagination`, `page_size=20`, `max_page_size=100`, `page_query_param='page'`
- [x] 1.3 Add platform serializer classes to `gimnasioApp/serializers.py`: `PlatformStatsSerializer`, `GimnasioPlatformSerializer`, `GimnasioPlatformDetailSerializer`, `UsuarioPlatformSerializer`, `MiembroActivoSerializer`, `PagoPlatformSerializer`

## Phase 2: Backend Core Implementation

- [x] 2.1 Add `PlatformStatsView` (APIView) to `gimnasioApp/views.py` — aggregates total_gimnasios, gimnasios_activos, total_usuarios_staff, demo_pendientes, demo_contactados, ingresos_mes_global (pagos+diarios), miembros_activos_global, retencion_promedio (weighted)
- [x] 2.2 Add `GimnasioPlatformViewSet` to `gimnasioApp/views.py` — `Gimnasio.objects.all()` with annotate (usuarios_count, miembros_activos_count, ingresos_mes), `get_serializer_class` switches list↔detail, search + is_active filters, `PlatformPagination`
- [x] 2.3 Register platform routes in `gimnasioApp/urls.py` — `platform/stats/` endpoint + `platform/gimnasios/` router with `IsSuperAdmin` permission
- [x] 2.4 Backend tests: `PlatformStatsTest` class in `gimnasioApp/tests.py` — test_superadmin_sees_all_gyms (403 for gym-admin), test_stats_aggregation_correct (ingresos=pagos+diarios, weighted retention), test_pagination_default_20_max_100, test_toggle_is_active PATCH

## Phase 3: Frontend Foundation

- [x] 3.1 Create `gimnasioReact/src/model/dto/platform.dto.ts` — TypeScript interfaces: `PlatformStats`, `GimnasioPlatform`, `GimnasioPlatformDetail`, `UsuarioPlatform`, `MiembroActivo`, `PagoPlatform`
- [x] 3.2 Create `gimnasioReact/src/api/action/platform.api.ts` — API client: `getPlatformStats`, `getGimnasiosPlatform`, `getGimnasioPlatformDetail`, `updateGimnasioPlatform`, `createGimnasioPlatform` using `axiosPrivate`
- [x] 3.3 Add Vitest configuration: update `gimnasioReact/vite.config.ts` with test config, add `vitest` + `@testing-library/react` + `jsdom` to `gimnasioReact/package.json` devDependencies

## Phase 4: Frontend Core Implementation

- [x] 4.1 Create `gimnasioReact/src/layouts/LayoutPlatform.tsx` — platform layout with header, `SideBarPlatform`, and `<Outlet />`
- [x] 4.2 Create `gimnasioReact/src/components/SideBarPlatform.tsx` — navigation sidebar: Dashboard, Gestión de Gimnasios links under `/platform/*`
- [x] 4.3 Create `gimnasioReact/src/pages/platform/PlatformDashboardPage.tsx` — 8 stat cards (total_gimnasios, gimnasios_activos, total_usuarios_staff, demo_pendientes, demo_contactados, ingresos_mes_global, miembros_activos_global, retencion_promedio) with loading skeletons + toasts
- [x] 4.4 Create `gimnasioReact/src/pages/platform/GymsManagementPage.tsx` — table with columns (name, address, phone, is_active, usuarios_count, miembros_activos_count, ingresos_mes), search input, pagination controls, is_active toggle PATCH without reload
- [x] 4.5 Create `gimnasioReact/src/pages/platform/GymDetailPage.tsx` — detail cards + usuarios table + miembros_activos table + ultimos_pagos table, route `/platform/gyms/:id`
- [x] 4.6 Add platform routes to `gimnasioReact/src/App.tsx` — wrap with `SuperAdminRoute`, add `LayoutPlatform` parent, nested routes: dashboard, gyms, gyms/:id

## Phase 5: Frontend Tests

- [x] 5.1 Create `gimnasioReact/src/__tests__/platform/PlatformDashboardPage.test.tsx` — renders stat cards and loads data (mock axios, assert 8 cards rendered)
- [x] 5.2 Create `gimnasioReact/src/__tests__/platform/platform.api.test.ts` — assert response shape for getPlatformStats, getGimnasiosPlatform returns paginated shape
- [x] 5.3 Create `gimnasioReact/src/__tests__/platform/GymsManagementPage.test.tsx` — renders table with pagination and toggle (mock axios, assert table rows, pagination buttons)
