# Design: Phase 1 Core Hardening

## Technical Approach

Eight independent tasks executed in dependency order: Task 1 (SQLite test infra) unblocks CI for all others. Tasks 2-3 are pure bug fixes. Task 4 adds a Python-level manager (no migration). Task 5 adds a model field with migration. Task 6 is documentation-only. Task 7 is test-only. Task 8 adds a soft-delete feature with backend+frontend coordination.

## Architecture Decisions

### Decision: SQLite In-Memory for Tests

**Choice**: Add `DATABASES['default']['TEST']` dict with `django.db.backends.sqlite3` and `NAME: ':memory:'`.
**Alternatives considered**: Separate test settings file, `TEST_RUNNER` override.
**Rationale**: Single-dict approach is Django-standard, no extra files. `:memory:` is fastest. Settings file already uses `dj_database_url` so the `TEST` dict cleanly overrides only during test runs.

### Decision: ActiveManager Pattern

**Choice**: Custom manager filtering `is_active=True` as default; keep original manager as `all_objects`.
**Alternatives considered**: `QuerySet.as_manager()`, filtering in each view's `get_queryset()`.
**Rationale**: Follows Django-conventional soft-delete pattern. Preserves `all_objects` for admin/reports. No view changes needed for standard queries. No migration required (Python-level only).

### Decision: Country Code on Gimnasio Model

**Choice**: `CharField(max_length=5, default='57')` on `Gimnasio`.
**Alternatives considered**: Setting in `settings.py`, separate config model.
**Rationale**: Per-gym configurability requires model field. `CharField` handles leading zeros (e.g., '001'). Default '57' preserves existing Colombian behavior. Single migration with default is safe for existing rows.

### Decision: Soft Delete via Estado Field

**Choice**: Override `destroy()` on `DemoRequestViewSet` to set `estado='cancelada'` instead of deleting.
**Alternatives considered**: `deleted_at` timestamp field, django.softdelete library.
**Rationale**: `DemoRequest` already has `estado` choices. Adding `'cancelada'` is minimal and consistent with existing state machine. No extra field, no library dependency. Preserves full audit trail.

## Task Dependency Graph

```
Task 1 (SQLite CI)
  ├── Task 2 (retencion_promedio fix)   ── independent ──┐
  ├── Task 3 (notified_at removal)      ── independent ──┤
  ├── Task 4 (ActiveManager)            ── independent ──┤
  ├── Task 5 (country_code)             ── independent ──┤
  ├── Task 6 (security audit)           ── independent ──┤
  ├── Task 7 (auth E2E test)            ── independent ──┤
  └── Task 8 (demo soft delete)         ── independent ──┘
```

All 8 tasks are independent. Task 1 is a prerequisite only for CI passing. Tasks 2-8 can run in parallel.

## Task 1: Testing Infrastructure

### Data Model Changes
None. Settings-only.

### File Changes

| File | Action | Description |
|------|--------|-------------|
| `gimnasio/settings.py` | Modify | Add `DATABASES['default']['TEST'] = {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}` |
| `.github/workflows/ci.yml` | Create | New workflow: ubuntu-latest, Python 3.12, pip install, `python manage.py test`, no MySQL service |

### Settings Change (settings.py)

Add after the existing `DATABASES` block:

```python
# Test database: SQLite in-memory for fast local and CI tests
if 'TEST' not in DATABASES.get('default', {}):
    DATABASES['default']['TEST'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
```

### CI Workflow (`.github/workflows/ci.yml`)

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -r requirements.txt
      - run: python manage.py test gimnasioApp
        env:
          SECRET_KEY: ci-test-key-not-for-production
          DATABASE_URL: ""
```

### Test Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Settings has correct TEST config | `self.assertEqual(settings.DATABASES['default']['TEST']['ENGINE'], 'django.db.backends.sqlite3')` |
| Integration | Full test suite runs on SQLite | `python manage.py test` completes in <10s |

### Rollback
Revert `settings.py` change; delete `.github/workflows/ci.yml`.

---

## Task 2: Platform Analytics — retencion_promedio Fix

### Data Model Changes
None.

### API Changes
`PlatformStatsSerializer.retencion_promedio` changes from default `coerce_to_string=True` to `coerce_to_string=False`.

### File Changes

| File | Action | Description |
|------|--------|-------------|
| `gimnasioApp/serializers.py` | Modify | Line 456: add `coerce_to_string=False` to `retencion_promedio` |
| `gimnasioReact/src/pages/admin/platform/PlatformDashboardPage.tsx` | Modify | Line 144: remove `.toFixed(1)` workaround, display `stats.retencion_promedio` directly |
| `gimnasioApp/tests.py` | Modify | Add test asserting `isinstance(data['retencion_promedio'], (int, float))` |

### Serializer Change

```python
# Before (line 456):
retencion_promedio = serializers.DecimalField(max_digits=5, decimal_places=1)

# After:
retencion_promedio = serializers.DecimalField(max_digits=5, decimal_places=1, coerce_to_string=False)
```

### Frontend Change

```tsx
// Before (line 144):
{Number(stats.retencion_promedio).toFixed(1)}%

// After:
{stats.retencion_promedio}%
```

### Test Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Serializer returns number | `assertIsInstance(data['retencion_promedio'], (int, float))` |
| Integration | API response contains number | DRF test client GET to `/platform/stats/` |

### Rollback
Revert serializer and frontend changes.

---

## Task 3: Data Cleanup — Remove notified_at

### Data Model Changes

Remove `notified_at` field from `MembresiaAsignada`. Generate `RemoveField` migration.

### Migration

```python
# Migration: remove notified_at from MembresiaAsignada
operations = [
    migrations.RemoveField(
        model_name='membresiaasignada',
        name='notified_at',
    ),
]
```

### File Changes

| File | Action | Description |
|------|--------|-------------|
| `gimnasioApp/models.py` | Modify | Remove line 182 (`notified_at = models.DateTimeField(...)`) |
| `gimnasioApp/migrations/XXXX_remove_notified_at.py` | Create | Auto-generated via `makemigrations` |
| `gimnasioApp/tests.py` | Modify | Add test: `MembresiaAsignada` has no `notified_at` attribute |

### Code Audit
Grep the codebase for `notified_at` references. The current codebase has:
- `models.py` line 182: field definition (remove)
- No references in views, serializers, or tests (confirmed by grep)

### Test Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `MembresiaAsignada` has no `notified_at` | `assertNotHasAttr(MembresiaAsignada, 'notified_at')` or `assert not hasattr` |
| Integration | Migration applies successfully | `call_command('migrate')` on test DB |
| Integration | `Notification` model unaffected | Existing notification tests pass |

### Rollback
Reverse migration: `python manage.py migrate gimnasioApp XXXX_previous`

---

## Task 4: Tenant Safety — ActiveManager

### Data Model Changes

Add `ActiveManager` class. Configure as default manager on `Gimnasio` and `Usuario`. Keep original managers as `all_objects`.

```python
class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)
```

On `Gimnasio`:
```python
objects = ActiveManager()
all_objects = models.Manager()
```

On `Usuario`:
```python
objects = ActiveManager()  # replaces UserManager
all_objects = UserManager()  # preserve UserManager as all_objects
```

**CRITICAL**: `Usuario` uses `UserManager` (extends `BaseUserManager`). `ActiveManager` must NOT replace `create_user`/`create_superuser`. Solution: `ActiveManager` only filters; `UserManager` remains accessible via `all_objects` for admin creation flows.

### File Changes

| File | Action | Description |
|------|--------|-------------|
| `gimnasioApp/models.py` | Modify | Add `ActiveManager` class; set `objects = ActiveManager()`, `all_objects = models.Manager()` on Gimnasio; on Usuario set `objects = ActiveManager()`, `all_objects = UserManager()` |
| `gimnasioApp/admin.py` | Modify | Ensure admin uses `all_objects` where needed |
| `gimnasioApp/views.py` | Audit | `Gimnasio.objects` usage in views (PlatformStatsView line 998-999 uses `Gimnasio.objects.count()` and `.filter(is_active=True)` — after ActiveManager, `.objects` already filters; audit for double-filtering) |
| `gimnasioApp/tests.py` | Modify | Add ActiveManager tests |

### Admin Impact

Current admin.py (not read but inferred): Django admin uses the default manager. After change, admin will only see active records. To show all, admin must use `all_objects`. Check and update admin classes if needed.

### Test Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `ActiveManager.get_queryset()` filters `is_active=True` | Create active + inactive records; assert `objects.all()` excludes inactive |
| Unit | `all_objects` returns all | `assertEqual(all_objects.count(), total_count)` |
| Integration | Auth fails for inactive user | Create inactive user; `authenticate()` returns None |
| Integration | PlatformStatsView still works | GET to platform stats returns correct counts |

### Rollback
Revert model changes; no migration needed (Python-level only).

---

## Task 5: Gym Country Code

### Data Model Changes

Add `country_code` field to `Gimnasio`:

```python
country_code = models.CharField(max_length=5, default='57', blank=True)
```

### Migration

```python
operations = [
    migrations.AddField(
        model_name='gimnasio',
        name='country_code',
        field=models.CharField(default='57', max_length=5, blank=True),
    ),
]
```

### Service Changes

Update `NotificationManager._construir_whatsapp_link()`:

```python
# Before (hardcoded):
PREFIJO_WHATSAPP = '57'
phone_clean = PREFIJO_WHATSAPP + phone_clean

# After (parameterized):
@staticmethod
def _construir_whatsapp_link(phone, wa_message, country_code='57'):
    phone_clean = ''.join(filter(str.isdigit, phone or ''))
    prefix = country_code or '57'
    if phone_clean and not phone_clean.startswith(prefix):
        phone_clean = prefix + phone_clean
    return f"https://wa.me/{phone_clean}?text={wa_message}" if phone_clean else None
```

Update `_crear_membresia` to pass `gimnasio.country_code`:

```python
whatsapp_link = cls._construir_whatsapp_link(
    membership.miembro.phone, wa_message, gimnasio.country_code
)
```

### File Changes

| File | Action | Description |
|------|--------|-------------|
| `gimnasioApp/models.py` | Modify | Add `country_code` field to `Gimnasio` |
| `gimnasioApp/migrations/XXXX_add_country_code.py` | Create | Auto-generated migration with default '57' |
| `gimnasioApp/services/notifications.py` | Modify | Parameterize `_construir_whatsapp_link` with `country_code` |
| `gimnasioApp/serializers.py` | Modify | `GimnasioSerializer` already uses `fields = '__all__'` — field auto-included |
| `gimnasioApp/tests.py` | Modify | Add country code tests |

### Test Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Default is '57' | `Gimnasio.objects.create(name='Test')` → `assertEqual(gym.country_code, '57')` |
| Unit | Custom code preserved | `Gimnasio.objects.create(name='US', country_code='1')` → `assertEqual(gym.country_code, '1')` |
| Unit | WhatsApp link uses country code | Mock phone; assert link starts with `https://wa.me/1` |
| Integration | Migration applies with default | Existing records get '57' |

### Rollback
Reverse migration: removes field, existing data preserved.

---

## Task 6: Security Audit — RegisterViewSet

### No Code Changes

This is a documentation-only task. Add docstring and threat model comments to `RegisterViewSet`.

### File Changes

| File | Action | Description |
|------|--------|-------------|
| `gimnasioApp/views.py` | Modify | Add docstring to `RegisterViewSet` explaining intentional `AllowAny`, threat model, and protections |

### Documentation Content

```python
class RegisterViewSet(APIView):
    """Public self-service registration endpoint.

    INTENTIONAL: This endpoint uses AllowAny permission to allow gym owners
    to create their account without prior authentication. This is by design.

    Threat Model:
    - Spam registrations: Mitigated by email uniqueness constraint and
      automatic gym creation (each registration creates a Gimnasio record).
      Rate limiting SHOULD be added in a future phase.
    - Abuse: Each registration creates a full gym + admin user. Consider
      CAPTCHA or email verification in future hardening.
    - Data exposure: Only returns user data for the created account.
      No cross-tenant data leakage possible.

    Protections in place:
    - Email uniqueness (database constraint + serializer validation)
    - Password hashing (set_password via AbstractBaseUser)
    - No sensitive data exposed in response
    """
    permission_classes = [AllowAny]
```

### Test Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Documentation exists | `assertIn('INTENTIONAL', RegisterViewSet.__doc__)` |
| Integration | Endpoint works as before | Existing registration tests pass |

### Rollback
Revert docstring changes.

---

## Task 7: User Auth — Forced Password Change E2E Test

### No Code Changes

This is a test-only task. Add comprehensive E2E test to `tests.py`.

### Test Flow

```
1. Create admin user with must_change_password=True
2. POST /gym/api/v1/token/ → get JWT access token
3. GET /api/user/ with token → expect 403 (must_change_password)
4. POST /auth/password/change/ with old+new password → expect 200
5. GET /api/user/ with same token → expect 200
```

### File Changes

| File | Action | Description |
|------|--------|-------------|
| `gimnasioApp/tests.py` | Modify | Add `ForcedPasswordChangeE2ETest` class with admin and recepcion scenarios |

### Test Implementation Outline

```python
class ForcedPasswordChangeE2ETest(TestCase):
    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Test Gym")
        self.admin = Usuario.objects.create_user(
            email="admin@test.com", name="Admin", lastname="User",
            password="oldpass123", roles="admin", gimnasio=self.gimnasio,
            must_change_password=True
        )

    def test_admin_forced_password_change_flow(self):
        # Step 1: Login → JWT token
        # Step 2: Access protected endpoint → 403
        # Step 3: POST /auth/password/change/ → 200
        # Step 4: Access protected endpoint → 200
```

### Test Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| E2E | Complete forced password change flow | `TestCase` with `APIRequestFactory` + `force_authenticate` + JWT token flow |
| E2E | Recepcion role same flow | Second test method with recepcion user |

### Rollback
Revert test additions.

---

## Task 8: Demo Request Soft Delete

### API Changes

Add `destroy()` method to `DemoRequestViewSet`. Override `http_method_names` to include `'delete'`.

### Data Model Changes

Add `'cancelada'` to `DemoRequest.ESTADOS` choices:

```python
ESTADOS = (
    ('pendiente', 'Pendiente'),
    ('contactado', 'Contactado'),
    ('cancelada', 'Cancelada'),
)
```

### Serializer Changes

Update `DemoRequestSerializer` to validate estado transitions:

```python
def validate_estado(self, value):
    if self.instance and self.instance.estado == 'cancelada':
        raise serializers.ValidationError("No se puede modificar una solicitud cancelada.")
    return value
```

### View Changes

```python
class DemoRequestViewSet(viewsets.ModelViewSet):
    # Add 'delete' to allowed methods
    http_method_names = ['get', 'post', 'patch', 'delete', 'options']

    def destroy(self, request, *args, **kwargs):
        demo = self.get_object()
        if demo.estado == 'cancelada':
            return Response(
                {'detail': 'La solicitud ya está cancelada.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        demo.estado = 'cancelada'
        demo.save(update_fields=['estado'])
        serializer = self.get_serializer(demo)
        return Response(serializer.data, status=status.HTTP_200_OK)
```

### Frontend Changes

**`demoRequests.api.ts`**: Add DELETE function:

```typescript
export const deleteDemoRequest = async (id: number): Promise<DemoRequest> => {
    const response = await axiosPrivate.delete<DemoRequest>(`/solicitudes-demo/${id}/`);
    return response.data;
};
```

**`DemoRequestsPage.tsx`**: Add delete button + confirmation modal:

- Add delete button in table row for `pendiente`/`contactado` states
- Add `ConfirmationModal` component (existing pattern in project)
- Add `useMutation` for delete with `onSuccess` invalidation
- Show toast on success: "Solicitud cancelada"

### File Changes

| File | Action | Description |
|------|--------|-------------|
| `gimnasioApp/models.py` | Modify | Add `'cancelada'` to `DemoRequest.ESTADOS` |
| `gimnasioApp/serializers.py` | Modify | Add `validate_estado` to `DemoRequestSerializer` |
| `gimnasioApp/views.py` | Modify | Add `destroy()` to `DemoRequestViewSet`, update `http_method_names` |
| `gimnasioApp/tests.py` | Modify | Add soft delete tests |
| `gimnasioReact/src/api/action/demoRequests.api.ts` | Modify | Add `deleteDemoRequest` function |
| `gimnasioReact/src/pages/admin/demo/DemoRequestsPage.tsx` | Modify | Add delete button + confirmation modal |

### Test Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `destroy()` sets `estado='cancelada'` | Create request; call destroy; assert `estado == 'cancelada'` |
| Unit | Cannot cancel already cancelled | Cancel twice; assert 400 on second |
| Unit | Serializer rejects invalid transitions | PATCH with `estado='cancelada'` on cancelled request → 400 |
| Integration | DELETE returns updated object | Assert response has `estado='cancelada'` and all fields preserved |
| Integration | Record persists in DB | `assertEqual(DemoRequest.objects.count(), 1)` after cancel |

### Rollback
Revert model, view, serializer, and frontend changes.

---

## Testing Strategy Summary

| Task | Unit | Integration | E2E |
|------|------|-------------|-----|
| 1. SQLite CI | Settings validation | Full suite on SQLite | CI workflow |
| 2. retencion_promedio | Serializer type check | API response type | Frontend display |
| 3. notified_at removal | Model attribute check | Migration applies | Full suite passes |
| 4. ActiveManager | Manager filtering | Auth + admin | Multi-tenant flow |
| 5. country_code | Default + custom | Migration + WhatsApp | Notification flow |
| 6. security audit | Docstring exists | Endpoint works | Registration works |
| 7. auth E2E | — | — | Login→403→change→200 |
| 8. soft delete | destroy + validation | DELETE endpoint | Cancel flow |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Migration / Rollout

| Task | Migration? | Rollback |
|------|-----------|----------|
| 1. SQLite CI | No | Revert settings |
| 2. retencion_promedio | No | Revert serializer |
| 3. notified_at | Yes (RemoveField) | Reverse migration |
| 4. ActiveManager | No (Python-only) | Revert model code |
| 5. country_code | Yes (AddField) | Reverse migration |
| 6. security audit | No | Revert docstring |
| 7. auth E2E | No | Revert test |
| 8. soft delete | No (choices only) | Revert code |

## Open Questions

- [ ] Does `admin.py` use a custom `ModelAdmin` for `Gimnasio`? If so, may need `list_display` update for `country_code`.
- [ ] Should `cancelada` DemoRequests be hidden from the default list view, or shown with a distinct badge?
- [ ] Is there an existing `ConfirmationModal` component in the React app, or should one be created?
