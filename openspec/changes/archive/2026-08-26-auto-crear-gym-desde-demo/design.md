# Design: Auto-create Gym from Demo Request

## Technical Approach

Extend `DemoRequestViewSet.perform_update` with atomic provisioning logic. When a SuperAdmin PATCHes `pendiente→contactado`, a service layer creates `Gimnasio` + admin `Usuario` inside `@transaction.atomic`. Post-commit sends welcome email synchronously. Reverse (`contactado→pendiente`) soft-deletes both entities. Frontend gains gym-aware toast and loading states on the badge.

## Architecture Decisions

### Decision: Service layer in `gimnasioApp/services/`

**Choice**: New files `onboarding.py` + `email.py` under existing `services/` dir.
**Alternatives**: Logic inline in ViewSet; separate Django app.
**Rationale**: Follows existing `services/notifications.py` pattern. Keeps ViewSet thin. Avoids new app overhead for ~150 lines of logic.

### Decision: Synchronous email post-commit

**Choice**: `transaction.on_commit` → `send_mail` (sync, fire-and-forget with logging).
**Alternatives**: Celery+Redis (async); email in same transaction.
**Rationale**: No worker infra exists. Low demo volume. Post-commit avoids blocking the response. Email failure logs + surfaces `email_sent=False` without rollback.

### Decision: Soft-delete on reverse

**Choice**: `gym.is_active=False`, `admin.is_active=False`, `demo.gym_creado=None`.
**Alternatives**: Hard delete; keep orphan gym.
**Rationale**: Reversible. Admin panel can reactivate. Avoids FK cascade issues. Follows existing `is_active` pattern on Gimnasio/Usuario.

### Decision: Forced password change via `must_change_password` field

**Choice**: New `Usuario.must_change_password` BooleanField. Backend middleware check + frontend redirect.
**Alternatives**: One-time token flow; separate password reset token.
**Rationale**: Simple. Reuses existing `/me/` profile endpoint. Frontend can detect in `AuthProvider.loadUser()` and redirect.

## Data Flow

```
SuperAdmin PATCH /solicitudes-demo/{id}/
  │
  ▼
DemoRequestViewSet.perform_update()
  │
  ├─ old=pendiente, new=contactado?
  │   ├─ provision_gym_from_demo(demo)  ← @transaction.atomic
  │   │   ├─ check email uniqueness → 400 if dup
  │   │   ├─ Gimnasio.objects.create(name, phone, address)
  │   │   ├─ Usuario.objects.create(email, name='Admin', lastname=truncated, roles='admin', must_change_password=True)
  │   │   ├─ demo.gym_creado = gym → demo.save()
  │   │   └─ return (gym, admin, temp_password)
  │   │
  │   └─ transaction.on_commit → send_welcome_email(gym, admin, temp_pass)
  │
  ├─ old=contactado, new=pendiente?
  │   └─ revert_gym_from_demo(demo)  ← soft-delete both, gym_creado=None
  │
  └─ else → serializer.save() (no-op provisioning)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `gimnasioApp/models.py` | Modify | Add `DemoRequest.gym_creado` FK (nullable, SET_NULL) + `Usuario.must_change_password` BooleanField(default=False) |
| `gimnasioApp/migrations/0012_*.py` | Create | Migration for both fields |
| `gimnasioApp/services/onboarding.py` | Create | `provision_gym_from_demo()`, `revert_gym_from_demo()`, `generate_temp_password()` |
| `gimnasioApp/services/email.py` | Create | `send_welcome_email()` using `django.core.mail.send_mail` |
| `gimnasioApp/views.py` | Modify | Override `DemoRequestViewSet.perform_update` with provisioning logic |
| `gimnasioApp/serializers.py` | Modify | `DemoRequestSerializer`: add `gym_creado` to read_only_fields; add `email_sent` SerializerMethodField |
| `gimnasio/settings.py` | Modify | Add EMAIL_BACKEND, DEFAULT_FROM_EMAIL, EMAIL_HOST* settings |
| `gimnasioApp/templates/emails/welcome_admin.html` | Create | HTML email template |
| `gimnasioApp/templates/emails/welcome_admin.txt` | Create | Plain text fallback |
| `gimnasioReact/src/api/action/demoRequests.api.ts` | Modify | Add `gym_creado?` to `DemoRequest` type |
| `gimnasioReact/src/pages/admin/demo/DemoRequestsPage.tsx` | Modify | Gym-aware toast, loading badge, error 400 handling |
| `gimnasioReact/src/model/dto/user.dto.ts` | Modify | Add `must_change_password?` to `AuthUser` |
| `gimnasioReact/src/context/AuthProvider.tsx` | Modify | Expose `must_change_password` from profile |
| `gimnasioReact/src/routes/protectedRoute/ProtectRoute.tsx` | Modify | Redirect to `/cambiar-password/` if `must_change_password` |
| `gimnasioReact/src/pages/auth/PasswordChangeRequiredPage.tsx` | Create | Forced password change form |
| `gimnasioApp/tests.py` | Modify | Unit + integration tests |

## Interfaces / Contracts

```python
# services/onboarding.py
def provision_gym_from_demo(demo_request: DemoRequest) -> tuple[Gimnasio, Usuario, str]:
    """Atomic: creates Gimnasio + admin Usuario + links demo.
    Returns (gym, admin_user, temp_password_plaintext).
    Raises ValidationError on duplicate email."""

def revert_gym_from_demo(demo_request: DemoRequest) -> None:
    """Soft-delete: gym.is_active=False, admin.is_active=False, demo.gym_creado=None."""

def generate_temp_password() -> str:
    """12-char URL-safe token via secrets.token_urlsafe."""

# services/email.py
def send_welcome_email(gym_id: int, admin_id: int, temp_password: str) -> None:
    """Sync send via send_mail. Logs success/failure. Never raises."""

# serializers.py — DemoRequestSerializer additions
email_sent = serializers.SerializerMethodField()  # read-only, from view context
```

```typescript
// demoRequests.api.ts — updated type
export type DemoRequest = {
  // ...existing fields...
  gym_creado?: { id: number; name: string } | null;
};

// user.dto.ts — AuthUser addition
export interface AuthUser {
  // ...existing fields...
  must_change_password?: boolean;
}
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `generate_temp_password` entropy/length; `provision_gym_from_demo` creates correct objects; `revert_gym_from_demo` soft-deletes | `django.test.TestCase` |
| Integration | PATCH pendiente→contactado creates gym+admin; idempotent re-PATCH; duplicate email → 400; reverse → soft-delete | `APIRequestFactory` + `force_authenticate` (superadmin) |
| Email | `send_welcome_email` called on commit; template context correct; failure logs + `email_sent=False` | Mock `send_mail` |
| Frontend | Badge loading state; gym-aware toast; error 400 toast; `must_change_password` redirect | RTL + mock API |

## Migration / Rollout

Single migration `0012` with two additive fields:
- `DemoRequest.gym_creado` — nullable FK, SET_NULL, no data loss
- `Usuario.must_change_password` — BooleanField(default=False), backward-compatible

No feature flags. Deploy backend first, then frontend. Existing demo requests unaffected (gym_creado=NULL).

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Open Questions

- [ ] Email: production SMTP provider (Resend/Mailgun/SendGrid) or keep console backend for now?
- [ ] Password change endpoint: new `POST /gym/api/v1/auth/password/change/` or reuse existing if added later?
