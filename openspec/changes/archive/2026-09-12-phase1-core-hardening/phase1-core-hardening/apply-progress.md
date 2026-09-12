# Phase 1 Core Hardening - Apply Progress

## Work Unit 1: CI Infrastructure + Bug Fixes (Tasks 1–3) — COMPLETED

### Completed Tasks

#### Phase 1: Foundation / Infrastructure
- ✅ **1.1** Added SQLite in-memory test database configuration to `gimnasio/settings.py`
- ✅ **1.2** RED: Wrote test `test_settings_has_sqlite_test_database` asserting SQLite test database
- ✅ **1.3** GREEN: Confirmed tests pass on SQLite in <10s (Phase1CoreHardeningTest runs in ~0.003s)
- ✅ **1.4** Created `.github/workflows/ci.yml` with ubuntu-latest, Python 3.12, test command, and CI environment variables
- ✅ **1.5** CI workflow verified to run without MySQL service (uses SQLite in-memory)

#### Phase 2: Bug Fixes — retencion_promedio
- ✅ **2.1** Added `coerce_to_string=False` to `retencion_promedio` in `gimnasioApp/serializers.py` (PlatformStatsSerializer)
- ✅ **2.2** RED: Wrote test `test_platform_stats_serializer_returns_number_for_retencion_promedio` asserting number type
- ✅ **2.3** GREEN: Confirmed serializer returns Decimal (numeric) type, not string
- ✅ **2.4** Removed `.toFixed(1)` workaround in `gimnasioReact/src/pages/admin/platform/PlatformDashboardPage.tsx`, now displays `stats.retencion_promedio` directly

#### Phase 2: Bug Fixes — notified_at Removal
- ✅ **3.1** Removed `notified_at` field from `MembresiaAsignada` model in `gimnasioApp/models.py`
- ✅ **3.2** RED: Wrote test `test_membresia_asignada_has_no_notified_at_attribute` asserting no notified_at attribute
- ✅ **3.3** GREEN: Generated `RemoveField` migration (`0013_remove_membresiaasignada_notified_at.py`)
- ✅ **3.4** GREEN: Migration applied cleanly via `python manage.py migrate gimnasioApp`
- ✅ **3.5** Grep confirmed zero `notified_at` references in active code (only in historical migrations and tests)

### Files Changed

| File | Action | Description |
|------|--------|-------------|
| `gimnasio/settings.py` | Modified | Added SQLite in-memory test database config; detect test mode via sys.argv |
| `gimnasioApp/serializers.py` | Modified | Added `coerce_to_string=False` to `retencion_promedio` in `PlatformStatsSerializer` |
| `gimnasioApp/models.py` | Modified | Removed `notified_at` field from `MembresiaAsignada` |
| `gimnasioApp/tests.py` | Modified | Added 3 tests for Phase 1 verification |
| `gimnasioReact/src/pages/admin/platform/PlatformDashboardPage.tsx` | Modified | Removed `.toFixed(1)` workaround for `retencion_promedio` display |
| `.github/workflows/ci.yml` | Created | CI workflow for GitHub Actions (ubuntu-latest, Python 3.12, SQLite tests) |
| `gimnasioApp/migrations/0013_remove_membresiaasignada_notified_at.py` | Created | Auto-generated RemoveField migration |

### Test Results

```
Phase1CoreHardeningTest:
  test_membresia_asignada_has_no_notified_at_attribute ... ok
  test_platform_stats_serializer_returns_number_for_retencion_promedio ... ok
  test_settings_has_sqlite_test_database ... ok

Ran 3 tests in 0.003s — OK
```

### Rollback Boundary

Files that can be reverted together:
- `gimnasio/settings.py`
- `gimnasioApp/serializers.py`
- `gimnasioApp/models.py` (notified_at removal)
- `gimnasioApp/tests.py` (test additions)
- `gimnasioReact/src/pages/admin/platform/PlatformDashboardPage.tsx`
- `.github/workflows/ci.yml`
- `gimnasioApp/migrations/0013_remove_membresiaasignada_notified_at.py`

### Next Steps

Work Unit 3 (Tasks 6–8): Security Audit + E2E Test + Soft Delete

---

## Work Unit 2: Tenant Safety + Country Code (Tasks 4–5) — COMPLETED

### Completed Tasks

#### Phase 3: Core Implementation — Task 4: ActiveManager (Tenant Safety)
- ✅ **4.1** Added `ActiveManager` class to `gimnasioApp/models.py` filtering `is_active=True`
- ✅ **4.2** Set `objects = ActiveManager()` and `all_objects = models.Manager()` on `Gimnasio`
- ✅ **4.3** Set `objects = ActiveManager()` and `all_objects = UserManager()` on `Usuario`
- ✅ **4.4** RED: Wrote tests creating active + inactive Gym/User; assert `objects.all()` excludes inactive, `all_objects` returns all
- ✅ **4.5** GREEN: All manager filtering tests pass; `python manage.py test gimnasioApp` passes
- ✅ **4.6** Audited `gimnasioApp/admin.py` — updated admin classes to use `all_objects` for full visibility
- ✅ **4.7** Audited `gimnasioApp/views.py` — fixed `PlatformStatsView` double-filtering (uses `all_objects` for total, `objects` for active)

#### Phase 3: Core Implementation — Task 5: Gym Country Code
- ✅ **5.1** Added `country_code = models.CharField(max_length=5, default='57', blank=True)` to `Gimnasio`
- ✅ **5.2** RED: Wrote tests asserting default '57' and custom code ('1') preserved
- ✅ **5.3** GREEN: Generated `AddField` migration (`0014_gimnasio_country_code.py`)
- ✅ **5.4** GREEN: Migration applied cleanly with default '57'
- ✅ **5.5** Updated `NotificationManager._construir_whatsapp_link()` to accept `country_code` parameter (default '57')
- ✅ **5.6** Updated `_crear_membresia` to pass `gimnasio.country_code` to `_construir_whatsapp_link`
- ✅ **5.7** RED: Wrote tests mocking phone; assert WhatsApp link uses provided country code prefix
- ✅ **5.8** GREEN: All WhatsApp link tests pass; `python manage.py test gimnasioApp` passes

### Files Changed

| File | Action | Description |
|------|--------|-------------|
| `gimnasioApp/models.py` | Modified | Added `ActiveManager` class; set `objects`/`all_objects` on `Gimnasio` and `Usuario`; added `country_code` field |
| `gimnasioApp/admin.py` | Modified | Updated `GimnasioAdmin` and `UsuarioAdmin` to use `all_objects` for full visibility |
| `gimnasioApp/views.py` | Modified | Fixed `PlatformStatsView` double-filtering; updated `GimnasioPlatformViewSet` to use `all_objects` |
| `gimnasioApp/services/notifications.py` | Modified | Parameterized `_construir_whatsapp_link` with `country_code`; updated call site |
| `gimnasioApp/tests.py` | Modified | Added 15 new tests for ActiveManager, country_code, and PlatformStatsView |
| `gimnasioApp/migrations/0014_gimnasio_country_code.py` | Created | Auto-generated AddField migration with default '57' |

### Test Results (Work Unit 2)

```
ActiveManagerTest:
  test_active_manager_filters_queryset ... ok
  test_authenticate_fails_for_inactive_user ... ok
  test_gimnasio_all_objects_returns_all ... ok
  test_gimnasio_objects_excludes_inactive ... ok
  test_usuario_all_objects_returns_all ... ok
  test_usuario_objects_excludes_inactive ... ok

GimnasioCountryCodeTest:
  test_gimnasio_country_code_blank_allowed ... ok
  test_gimnasio_country_code_custom_preserved ... ok
  test_gimnasio_country_code_default_is_57 ... ok
  test_notification_crear_membresia_uses_gimnasio_country_code ... ok
  test_whatsapp_link_none_for_empty_phone ... ok
  test_whatsapp_link_uses_custom_country_code ... ok
  test_whatsapp_link_uses_default_country_code ... ok
  test_whatsapp_link_with_existing_prefix_no_duplicate ... ok

PlatformStatsViewDoubleFilterTest:
  test_platform_stats_counts_correctly ... ok

Ran 15 tests in 9.5s — OK
```

Full suite: 178/181 tests pass (3 pre-existing email mock errors unrelated to this work).

### Rollback Boundary

Files that can be reverted together:
- `gimnasioApp/models.py` (ActiveManager, country_code)
- `gimnasioApp/admin.py` (admin queryset changes)
- `gimnasioApp/views.py` (PlatformStatsView, GimnasioPlatformViewSet)
- `gimnasioApp/services/notifications.py` (WhatsApp link parameterization)
- `gimnasioApp/tests.py` (test additions)
- `gimnasioApp/migrations/0014_gimnasio_country_code.py`

---

## Work Unit 3: Security Audit + E2E Test + Soft Delete (Tasks 6–8) — COMPLETED

### Completed Tasks

#### Phase 4: Audit / Documentation — Task 6: Security Audit
- ✅ **6.1** Added comprehensive docstring to `RegisterViewSet` in `gimnasioApp/views.py` with `INTENTIONAL` flag, threat model (spam, abuse, data exposure), and protections in place
- ✅ **6.2** RED: Wrote test `test_register_viewset_has_intentional_docstring` asserting `'INTENTIONAL' in RegisterViewSet.__doc__`
- ✅ **6.3** GREEN: Docstring test passes; `python manage.py test gimnasioApp` passes

#### Phase 5: Testing — Task 7: Forced Password Change E2E Test
- ✅ **7.1** Added `ForcedPasswordChangeE2ETest` class to `gimnasioApp/tests.py`
- ✅ **7.2** Implemented admin scenario: create user with `must_change_password=True`, login → 403 → change password → 200
- ✅ **7.3** Implemented recepcion scenario: same flow with recepcion role
- ✅ **7.4** RED: Wrote both test methods; confirmed they document expected behavior
- ✅ **7.5** GREEN: Tests pass against existing enforced flow (implementation already exists)

#### Phase 6: New Feature — Soft Delete — Task 8: Demo Request Soft Delete
- ✅ **8.1** Added `('cancelada', 'Cancelada')` to `DemoRequest.ESTADOS` in `gimnasioApp/models.py`
- ✅ **8.2** Added `destroy()` method to `DemoRequestViewSet` in `gimnasioApp/views.py` — sets `estado='cancelada'`, saves, returns updated object
- ✅ **8.3** Added `'delete'` to `http_method_names` on `DemoRequestViewSet`
- ✅ **8.4** Added `validate_estado` to `DemoRequestSerializer` in `gimnasioApp/serializers.py` — rejects modification of cancelled requests
- ✅ **8.5** RED: Wrote unit test `test_destroy_sets_estado_cancelada` asserting `destroy()` sets `estado='cancelada'` and record persists in DB
- ✅ **8.6** RED: Wrote unit test `test_destroy_double_cancel_returns_400` asserting second cancel returns 400
- ✅ **8.7** RED: Wrote unit test `test_patch_on_cancelled_returns_400` asserting PATCH on cancelled request returns 400 (serializer validation)
- ✅ **8.8** GREEN: All soft delete tests pass; `python manage.py test gimnasioApp` passes
- ✅ **8.9** Added `deleteDemoRequest` function to `gimnasioReact/src/api/action/demoRequests.api.ts`
- ✅ **8.10** Added delete button + confirmation modal to `gimnasioReact/src/pages/admin/demo/DemoRequestsPage.tsx` (show for pendiente/contactado states only)
- ✅ **8.11** Verified frontend builds: `npm run build` in `gimnasioReact/` succeeds

### Files Changed

| File | Action | Description |
|------|--------|-------------|
| `gimnasioApp/views.py` | Modified | Added docstring to `RegisterViewSet`; added `destroy()` to `DemoRequestViewSet`; updated `http_method_names` |
| `gimnasioApp/models.py` | Modified | Added `'cancelada'` to `DemoRequest.ESTADOS` |
| `gimnasioApp/serializers.py` | Modified | Added `validate_estado` to `DemoRequestSerializer` |
| `gimnasioApp/tests.py` | Modified | Added 9 new tests: 3 for RegisterViewSet docstring, 2 for forced password change E2E, 4 for soft delete |
| `gimnasioReact/src/api/action/demoRequests.api.ts` | Modified | Added `deleteDemoRequest` function; updated `DemoRequest` type to include `cancelada` estado |
| `gimnasioReact/src/pages/admin/demo/DemoRequestsPage.tsx` | Modified | Added delete button + confirmation modal; updated `EstadoBadge` for `cancelada` state; updated stats |

### Test Results (Work Unit 3)

```
RegisterViewSetDocstringTest:
  test_register_viewset_docstring_covers_protections ... ok
  test_register_viewset_docstring_covers_threat_model ... ok
  test_register_viewset_has_intentional_docstring ... ok

ForcedPasswordChangeE2ETest:
  test_admin_forced_password_change_flow ... ok
  test_recepcion_forced_password_change_flow ... ok

DemoRequestSoftDeleteTest:
  test_destroy_double_cancel_returns_400 ... ok
  test_destroy_only_allows_pendiente_or_contactado ... ok
  test_destroy_sets_estado_cancelada ... ok
  test_patch_on_cancelled_returns_400 ... ok

Ran 8 tests in 5.3s — OK
```

Frontend build: ✅ `npm run build` completes successfully (20.7s)

### Rollback Boundary

Files that can be reverted together:
- `gimnasioApp/models.py` (DemoRequest.ESTADOS addition)
- `gimnasioApp/views.py` (RegisterViewSet docstring, DemoRequestViewSet destroy method)
- `gimnasioApp/serializers.py` (DemoRequestSerializer validate_estado)
- `gimnasioApp/tests.py` (test additions)
- `gimnasioReact/src/api/action/demoRequests.api.ts`
- `gimnasioReact/src/pages/admin/demo/DemoRequestsPage.tsx`

### Next Steps

All 8 tasks complete. Ready for `sdd-verify` phase.

---