# Proposal: Phase 1 Core Hardening

## Intent

Harden the ControlFit foundation by fixing critical bugs, removing technical debt, and adding safety defaults before building new features. This phase addresses SQLite test performance, serializer bugs, deprecated columns, missing soft-delete patterns, and configurable WhatsApp prefixes — all blocking reliable CI and multi-tenant safety.

## Scope

### In Scope
- SQLite test runner configuration (CI + local)
- `retencion_promedio` DecimalField serialization fix
- Drop `notified_at` column from `MembresiaAsignada`
- ActiveManager for `Gimnasio`/`Usuario` with `is_active` default
- Configurable WhatsApp country code per gym
- RegisterViewSet public access audit (no code change)
- E2E test for forced password change flow
- Soft delete for DemoRequest (`estado='cancelada'`)

### Out of Scope
- New business features beyond listed tasks
- Frontend redesign or new UI components
- Database migration strategy beyond listed items
- Authentication/authorization refactor

## Capabilities

### New Capabilities
- `demo-request-soft-delete`: Soft-delete pattern for demo requests with audit trail
- `gym-country-code`: Per-gym WhatsApp country code configuration

### Modified Capabilities
- `user-auth`: Forced password change flow verification
- `platform-analytics`: `retencion_promedio` returns number not string
- `tenant-safety`: ActiveManager default filtering for multi-tenant isolation

## Approach

Execute 8 independent tasks with minimal dependencies. Task 1 (SQLite) unblocks CI for all others. Tasks 2, 3, 7 are pure bug fixes/cleanup. Task 4 adds safety default. Task 5 adds configuration. Task 6 is audit-only. Task 8 adds new soft-delete feature. Parallelize where possible.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `gimnasio/settings.py` | Modified | Add TEST dict for SQLite |
| `.github/workflows/ci.yml` | Modified | Remove MySQL service |
| `gimnasioApp/serializers.py` | Modified | Fix DecimalField, validate estado transition |
| `gimnasioApp/models.py` | Modified | Remove notified_at, add ActiveManager, add country_code |
| `gimnasioApp/views.py` | Modified | Add destroy to DemoRequestViewSet, audit RegisterViewSet |
| `gimnasioApp/services/notifications.py` | Modified | Use gym.country_code |
| `gimnasioApp/tests.py` | Modified | Add E2E forced password test |
| `gimnasioReact/src/pages/admin/platform/PlatformDashboardPage.tsx` | Modified | Remove .toFixed() workaround |
| `gimnasioReact/src/pages/admin/demo/DemoRequestsPage.tsx` | Modified | Add delete button + modal |
| `gimnasioReact/src/api/action/demoRequests.api.ts` | Modified | Add DELETE call |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| ActiveManager breaks existing admin queries | Medium | Audit all `.objects` usage; update admin views to use `all_objects` |
| SQLite migration differs from MySQL behavior | Low | ORM-only tests; no raw SQL fixtures |
| WhatsApp prefix change breaks existing links | Low | Default '57' preserves current behavior |
| Soft delete requires frontend coordination | Medium | Single PR with backend + frontend changes |

## Rollback Plan

1. Revert migrations: `python manage.py migrate gimnasioApp 000X_previous`
2. Revert settings.py TEST config
3. Revert serializer/model/view changes via git
4. Frontend: revert API calls and UI components

## Dependencies

- Django 5.2 test runner SQLite support
- Existing `Notification` model (Nivel 1) already stores notification timestamps

## Success Criteria

- [ ] `python manage.py test` completes in <10s locally on SQLite
- [ ] CI passes without MySQL service
- [ ] Frontend receives `retencion_promedio` as number (no .toFixed() needed)
- [ ] `notified_at` column removed; no code references remain
- [ ] `Gimnasio.objects.all()` returns only active gyms; `all_objects` returns all
- [ ] WhatsApp links use `gimnasio.country_code` (default '57')
- [ ] RegisterViewSet audit confirms intentional public access
- [ ] E2E test covers login → 403 → password change → 200 access
- [ ] SuperAdmin can cancel demo request; request persists with `estado='cancelada'`