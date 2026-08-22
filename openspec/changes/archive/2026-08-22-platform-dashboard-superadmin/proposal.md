# Proposal: Platform Dashboard for SuperAdmin

## Intent
Give the SaaS owner (SuperAdmin, `request.gimnasio = None`) a global, multi-tenant-free control plane: aggregated platform metrics, gym management (list/detail/activate/create), and demo-request visibility — without leaking tenant scoping.

## Scope
### In Scope
- Backend: `IsSuperAdmin` permission; `PlatformStatsView` (GET `/platform/stats/`); `GimnasioPlatformViewSet` (NO `MultiTenantViewSetMixin`) with list/detail serializers + `is_active` PATCH + create; `PlatformPagination` (page 20, max 100); Django tests.
- Frontend: `platform.dto.ts`, `platform.api.ts`, `LayoutPlatform`, `SideBarPlatform`, `PlatformDashboardPage`, `GymsManagementPage`, `GymDetailPage`; routes under `SuperAdminRoute`; Vitest+jsdom tests scoped to platform module.
### Out of Scope
- Admin-user creation on gym POST (follow-up); Stripe/billing; audit logs; global push/email.

## Capabilities
### New Capabilities
- `platform-api`: SuperAdmin-only backend — stats aggregation + gym list/retrieve/patch/create, `IsSuperAdmin`, scoped `PlatformPagination`.
- `platform-frontend`: Platform layout, sidebar, dashboard/gyms/detail pages, API client, DTOs, routes, Vitest tests.

## Approach
- Permission `IsSuperAdmin` (role == 'superadmin') applied with `IsAuthenticated` to all `/platform/*` views.
- `GimnasioPlatformViewSet` queries `Gimnasio.objects.all()` with `Count`/`Sum` annotations (no N+1); `get_serializer_class` switches list↔detail; create uses base `GimnasioSerializer` (no gimnasio needed).
- `PlatformStatsView`: ORM `Count`/`Sum`; `ingresos_mes_global = PagoMembresia + UsuarioGymDay` (parity with Home); `retencion_promedio` = avg of per-gym retention helper.
- Frontend reuses existing UI primitives; calls `/gym/api/v1/platform/...` via `axiosPrivate`; loading skeletons + toasts; Vitest for 3 component/API tests.

## Affected Areas
| Area | Impact | Description |
|------|--------|-------------|
| `gimnasioApp/permissions.py` | Modified | add `IsSuperAdmin` |
| `gimnasioApp/views.py` | Modified | `PlatformStatsView`, `GimnasioPlatformViewSet` |
| `gimnasioApp/serializers.py` | Modified | `GimnasioPlatformSerializer`, `…DetailSerializer`, `PlatformStatsSerializer` |
| `gimnasioApp/urls.py` | Modified | `platform/` routes + router |
| `gimnasio/settings.py` | Modified | `PlatformPagination` class |
| `gimnasioApp/tests.py` | Modified | platform tests |
| `gimnasioReact/src/...` | New | layout/sidebar/pages/api/dto/tests |
| `gimnasioReact/package.json` + vitest config | Modified | test runner |

## Risks
| Risk | Likelihood | Mitigation |
| Tenant leakage (empty list) | Med | never extend mixin; test asserts superadmin sees all |
| N+1 per-gym metrics | Med | annotate + page cap |
| Serializer assumes gimnasio | Med | dedicated platform serializers |
| No frontend test runner | Low | Vitest scoped to platform |

## Rollback Plan
Feature is additive (new endpoints/serializers/routes, new files). Revert by removing platform URLs/router entry, `IsSuperAdmin`, `PlatformPagination`, and the `platform/*` frontend routes/files; no DB migration. No data migration required.

## Dependencies
- Existing models (`Gimnasio`, `Usuario`, `PagoMembresia`, `UsuarioGymDay`, `DemoRequest`) cover all data.
- Vitest + jsdom (dev dependency) for frontend tests.

## Success Criteria
- [ ] SuperAdmin reaches `/platform/dashboard` (AC1 already done)
- [ ] Dashboard shows >=6 global cards (AC2)
- [ ] Gym table paginated 20/page with required columns (AC3)
- [ ] Gym detail route shows metrics + active members + recent payments (AC4)
- [ ] `is_active` toggle PATCH updates UI without reload (AC5)
- [ ] `POST /platform/gimnasios/` creates gym; admin registered later (AC6)
- [ ] Gym-admin gets 403 on all `/platform/*` (AC7)
- [ ] Backend `pytest -k platform` passes (AC8)
- [ ] Frontend `npm test -- platform` passes (AC9)
