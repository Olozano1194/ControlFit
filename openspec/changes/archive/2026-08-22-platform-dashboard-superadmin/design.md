# Design: Platform Dashboard for SuperAdmin

## Technical Approach

SuperAdmin gets a dedicated `/platform/*` API namespace (no `MultiTenantViewSetMixin`) backed by `IsSuperAdmin` permission. Backend aggregates platform-wide stats via annotated ORM queries; frontend mirrors the existing `LayoutAdmin` pattern with a new `LayoutPlatform` + `SideBarPlatform`. Vitest added for frontend test coverage.

## Architecture Decisions

### Decision: Retention Formula — Weighted Average

**Choice**: Weighted average = `SUM(active_today) / SUM(active_prev_month) * 100`
**Alternatives considered**: Simple average of per-gym retention percentages
**Rationale**: Simple average treats a 2-member gym and a 200-member gym equally. Weighted reflects actual platform retention.

### Decision: Ingresos Mes = Pagos + Diarios

**Choice**: `ingresos_mes = SUM(PagoMembresia.monto) + SUM(UsuarioGymDay.price)` for current month
**Alternatives considered**: MembresiaAsignada.price (expected revenue)
**Rationale**: Matches existing Home view formula — represents actual money received, not contractual amounts.

### Decision: GimnasioPlatformViewSet — No MultiTenantViewSetMixin

**Choice**: Direct `Gimnasio.objects.all()` queryset with `IsSuperAdmin` permission guard
**Alternatives considered**: Reusing `MultiTenantViewSetMixin` with superadmin bypass
**Rationale**: The mixin's bypass logic (`roles == 'superadmin'`) is implicit. A dedicated ViewSet without the mixin is explicit about cross-tenant access and avoids accidental scoping if the mixin changes.

### Decision: Frontend Vitest (not Jest)

**Choice**: Vitest + jsdom, scoped to `gimnasioReact/`
**Alternatives considered**: Jest, no frontend tests
**Rationale**: Proposal R4. Vite-native, zero-config with existing `vite.config.ts`. Faster than Jest in Vite projects.

### Decision: Pagination — PageNumberPagination Class

**Choice**: `PlatformPagination` with `page_size=20`, `max_page_size=100`
**Alternatives considered**: LimitOffsetPagination
**Rationale**: Page-based is simpler for table UIs. Matches DRF defaults the project already uses.

## Data Flow

```
Frontend                          Backend                         DB
-------                           -------                         --
PlatformDashboardPage
  |-- getPlatformStats() ------> PlatformStatsView
  |                              |-- Gimnasio.objects.count()
  |                              |-- Usuario.objects.filter(roles__in=[...]).count()
  |                              |-- DemoRequest aggregation
  |                              |-- PagoMembresia aggregation (month)
  |                              |-- UsuarioGymDay aggregation (month)
  |                              +-- Weighted retention calc
  |                              <-- PlatformStatsSerializer
  +-- renders 8 stat cards

GymsManagementPage
  |-- getGimnasiosPlatform() --> GimnasioPlatformViewSet.list
  |                              |-- annotate(usuarios_count, miembros_activos_count, ingresos_mes)
  |                              |-- PlatformPagination (page=20)
  |                              +-- search / is_active filters
  |                              <-- Paginated GimnasioPlatformSerializer
  +-- renders table + toggle

GymDetailPage (route: /platform/gyms/:id)
  |-- getGimnasioPlatformDetail() -> GimnasioPlatformViewSet.retrieve
  |                                  |-- annotate + nested relations
  |                                  <-- GimnasioPlatformDetailSerializer
  +-- renders detail cards + members + payments

  updateGimnasioPlatform(id, {is_active}) -> PATCH -> Gimnasio.is_active
  createGimnasioPlatform(data)            -> POST  -> Gimnasio (no admin assigned)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `gimnasioApp/permissions.py` | Modify | Add `IsSuperAdmin` permission class |
| `gimnasioApp/serializers.py` | Modify | Add PlatformStatsSerializer, GimnasioPlatformSerializer, GimnasioPlatformDetailSerializer, UsuarioPlatformSerializer, MiembroActivoSerializer, PagoPlatformSerializer |
| `gimnasioApp/views.py` | Modify | Add PlatformStatsView, GimnasioPlatformViewSet |
| `gimnasioApp/urls.py` | Modify | Register platform/ router + stats endpoint |
| `gimnasioApp/tests.py` | Modify | Add platform test class (4 test methods) |
| `gimnasioReact/src/model/dto/platform.dto.ts` | Create | TypeScript interfaces for all platform DTOs |
| `gimnasioReact/src/api/action/platform.api.ts` | Create | API client functions for platform endpoints |
| `gimnasioReact/src/layouts/LayoutPlatform.tsx` | Create | Platform layout (sidebar + header + outlet) |
| `gimnasioReact/src/components/SideBarPlatform.tsx` | Create | SuperAdmin sidebar navigation |
| `gimnasioReact/src/pages/platform/PlatformDashboardPage.tsx` | Create | Dashboard page with 8 stat cards |
| `gimnasioReact/src/pages/platform/GymsManagementPage.tsx` | Create | Gym list with table, search, pagination, toggle |
| `gimnasioReact/src/pages/platform/GymDetailPage.tsx` | Create | Gym detail with metrics, members, payments |
| `gimnasioReact/src/App.tsx` | Modify | Add platform routes under SuperAdminRoute |
| `gimnasioReact/vite.config.ts` | Modify | Add Vitest test configuration |
| `gimnasioReact/package.json` | Modify | Add vitest + jsdom dev dependencies |
| `gimnasioReact/src/__tests__/platform/` | Create | Vitest tests for platform module |

## Interfaces / Contracts

### Backend — Permissions

```python
class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.roles == 'superadmin'
        )
```

### Backend — Serializers

```python
class PlatformStatsSerializer(serializers.Serializer):
    total_gimnasios = serializers.IntegerField()
    gimnasios_activos = serializers.IntegerField()
    total_usuarios_staff = serializers.IntegerField()
    demo_pendientes = serializers.IntegerField()
    demo_contactados = serializers.IntegerField()
    ingresos_mes_global = serializers.DecimalField(max_digits=14, decimal_places=2)
    miembros_activos_global = serializers.IntegerField()
    retencion_promedio = serializers.DecimalField(max_digits=5, decimal_places=1)

class GimnasioPlatformSerializer(serializers.ModelSerializer):
    usuarios_count = serializers.IntegerField(read_only=True)
    miembros_activos_count = serializers.IntegerField(read_only=True)
    ingresos_mes = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    class Meta:
        model = Gimnasio
        fields = ['id', 'name', 'address', 'phone', 'is_active', 'created_at',
                  'usuarios_count', 'miembros_activos_count', 'ingresos_mes']

class GimnasioPlatformDetailSerializer(GimnasioPlatformSerializer):
    usuarios = UsuarioPlatformSerializer(many=True, read_only=True)
    miembros_activos = MiembroActivoSerializer(many=True, read_only=True)
    ultimos_pagos = PagoPlatformSerializer(many=True, read_only=True)
```

### Backend — API Endpoints

| Method | Path | Request | Response |
|--------|------|---------|----------|
| GET | `/gym/api/v1/platform/stats/` | — | `PlatformStatsSerializer` |
| GET | `/gym/api/v1/platform/gimnasios/` | `?page=1&page_size=20&search=xxx&is_active=true` | Paginated `GimnasioPlatformSerializer` |
| GET | `/gym/api/v1/platform/gimnasios/{id}/` | — | `GimnasioPlatformDetailSerializer` |
| PATCH | `/gym/api/v1/platform/gimnasios/{id}/` | `{is_active?, name?, address?, phone?}` | `GimnasioPlatformDetailSerializer` |
| POST | `/gym/api/v1/platform/gimnasios/` | `{name, address?, phone?}` | `GimnasioPlatformDetailSerializer` (201) |

### Backend — PlatformPagination

```python
class PlatformPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'
```

### Backend — GimnasioPlatformViewSet Queryset Annotations

```python
from django.db.models import Count, Sum, Q
from datetime import date

today = date.today()
month = today.month
year = today.year

Gimnasio.objects.annotate(
    usuarios_count=Count('usuarios', filter=Q(usuarios__is_active=True)),
    miembros_activos_count=Count(
        'miembros__membresias_asignadas',
        filter=Q(
            miembros__membresias_asignadas__dateInitial__lte=today,
            miembros__membresias_asignadas__dateFinal__gte=today,
            miembros__membresias_asignadas__is_active=True
        )
    ),
    ingresos_mes=Sum(
        'miembros__membresias_asignadas__pagos__monto',
        filter=Q(
            miembros__membresias_asignadas__pagos__fecha_pago__month=month,
            miembros__membresias_asignadas__pagos__fecha_pago__year=year
        )
    ) + Sum(
        'miembros_diarios__price',
        filter=Q(
            miembros_diarios__dateInitial__month=month,
            miembros_diarios__dateInitial__year=year
        )
    )
)
```

### Frontend — DTOs (platform.dto.ts)

```typescript
export interface PlatformStats {
  total_gimnasios: number;
  gimnasios_activos: number;
  total_usuarios_staff: number;
  demo_pendientes: number;
  demo_contactados: number;
  ingresos_mes_global: number;
  miembros_activos_global: number;
  retencion_promedio: number;
}

export interface GimnasioPlatform {
  id: number;
  name: string;
  address: string;
  phone: string;
  is_active: boolean;
  created_at: string;
  usuarios_count: number;
  miembros_activos_count: number;
  ingresos_mes: number;
}

export interface GimnasioPlatformDetail extends GimnasioPlatform {
  usuarios: UsuarioPlatform[];
  miembros_activos: MiembroActivo[];
  ultimos_pagos: PagoPlatform[];
}

export interface UsuarioPlatform {
  id: number;
  email: string;
  name: string;
  lastname: string;
  roles: string;
  is_active: boolean;
}

export interface MiembroActivo {
  id: number;
  name: string;
  lastname: string;
  membresia: string;
  dateFinal: string;
  saldo_pendiente: number;
}

export interface PagoPlatform {
  id: number;
  monto: number;
  fecha_pago: string;
  metodo_pago: string;
  miembro_name: string;
  membresia_name: string;
}
```

### Frontend — API Client (platform.api.ts)

```typescript
import { axiosPrivate } from '../axios/axios.private';
import { PlatformStats, GimnasioPlatform, GimnasioPlatformDetail } from '../../model/dto/platform.dto';

export const getPlatformStats = () =>
  axiosPrivate.get<PlatformStats>('/platform/stats/');

export const getGimnasiosPlatform = (params?: {
  page?: number;
  page_size?: number;
  search?: string;
  is_active?: boolean;
}) => axiosPrivate.get<{ results: GimnasioPlatform[]; count: number }>(
  '/platform/gimnasios/', { params }
);

export const getGimnasioPlatformDetail = (id: number) =>
  axiosPrivate.get<GimnasioPlatformDetail>(`/platform/gimnasios/${id}/`);

export const updateGimnasioPlatform = (id: number, data: Partial<GimnasioPlatform>) =>
  axiosPrivate.patch<GimnasioPlatformDetail>(`/platform/gimnasios/${id}/`, data);

export const createGimnasioPlatform = (data: { name: string; address?: string; phone?: string }) =>
  axiosPrivate.post<GimnasioPlatformDetail>('/platform/gimnasios/', data);
```

### Frontend — Routes (App.tsx additions)

```tsx
{/* Rutas de la plataforma — solo superadmin */}
<Route element={<SuperAdminRoute />}>
  <Route path="platform" element={<LayoutPlatform />}>
    <Route path="dashboard" element={<PlatformDashboardPage />} />
    <Route path="gyms" element={<GymsManagementPage />} />
    <Route path="gyms/:id" element={<GymDetailPage />} />
  </Route>
</Route>
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Backend Unit | `IsSuperAdmin` permission: superadmin passes, gym-admin returns 403 | `APIRequestFactory` + `force_authenticate` |
| Backend Unit | Stats aggregation: ingresos = pagos + diarios, retention weighted | `TestCase` with 2+ gyms, manual assertions |
| Backend Unit | Pagination defaults: page_size=20, max=100 | `TestCase` with 25 gym records |
| Backend Unit | PATCH is_active toggle | `APIRequestFactory` + `force_authenticate` |
| Frontend Unit | `PlatformDashboardPage` renders cards + loads data | Vitest + jsdom, mock axios |
| Frontend Unit | API client shape: `getPlatformStats`, `getGimnasiosPlatform` | Vitest, assert response shape |
| Frontend Unit | `GymsManagementPage` pagination + toggle | Vitest + jsdom, mock axios |

### Backend Test Cases (tests.py)

```python
class PlatformStatsTest(TestCase):
    def test_superadmin_sees_all_gyms(self):
        """SuperAdmin sees all gyms; gym-admin gets 403."""

    def test_stats_aggregation_correct(self):
        """ingresos = pagos + diarios; retencion is weighted average."""

    def test_pagination_default_20_max_100(self):
        """Page size defaults to 20, max capped at 100."""

    def test_toggle_is_active(self):
        """PATCH is_active toggles gym state."""
```

### Frontend Test Cases (Vitest)

```typescript
// src/__tests__/platform/PlatformDashboardPage.test.tsx
describe('PlatformDashboardPage', () => {
  it('renders stat cards and loads data', () => { ... });
});

// src/__tests__/platform/platform.api.test.ts
describe('platform API client', () => {
  it('getPlatformStats returns correct shape', () => { ... });
  it('getGimnasiosPlatform returns paginated shape', () => { ... });
});

// src/__tests__/platform/GymsManagementPage.test.tsx
describe('GymsManagementPage', () => {
  it('renders table with pagination and toggle', () => { ... });
});
```

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Migration / Rollout

No migration required. Feature is fully additive: new endpoints, serializers, permissions, frontend routes, and components. No DB schema changes — all data comes from existing models (`Gimnasio`, `Usuario`, `PagoMembresia`, `UsuarioGymDay`, `DemoRequest`).

## Open Questions

- None — all decisions resolved per proposal inputs.