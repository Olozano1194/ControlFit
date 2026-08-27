# Tasks: Auto-create Gym from Demo Request

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 420–480 |
| 400-line budget risk | Medium |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (backend core) → PR 2 (email + templates) → PR 3 (frontend) |
| Delivery strategy | ask-on-risk |
| Chain strategy | feature-branch-chain |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Backend core: models, migration, onboarding service, viewset, serializer, tests | PR 1 | `python manage.py test gimnasioApp` | Manual PATCH via DRF browsable API or curl | `gimnasioApp/models.py`, `views.py`, `services/onboarding.py`, `serializers.py`, migration |
| 2 | Email service: email.py, templates, settings.py, email tests | PR 2 | `python manage.py test gimnasioApp` | Mock SMTP console backend | `gimnasioApp/services/email.py`, `templates/emails/*`, `settings.py` |
| 3 | Frontend: types, DemoRequestsPage, AuthProvider, ProtectedRoute, PasswordChangeRequiredPage, toast utils, tests | PR 3 | `npm run build && npm run lint` | Manual browser: toggle estado badge | `gimnasioReact/src/` files |

## Phase 1: Foundation (Models + Migration)

- [x] 1.1 Add `gym_creado` FK to `DemoRequest` in `gimnasioApp/models.py` — nullable, `SET_NULL`, related_name=`demo_origen`
- [x] 1.2 Add `must_change_password` BooleanField(default=False) to `Usuario` in `gimnasioApp/models.py`
- [x] 1.3 Run `makemigrations` → create migration `0012_*` with both fields
- [x] 1.4 Run `migrate` — verify zero-downtime (additive nullable fields only)
- [x] 1.5 Update `DemoRequestSerializer` in `gimnasioApp/serializers.py` to include `gym_creado` nested (read_only)

## Phase 2: Backend Core (Service Layer + ViewSet)

- [x] 2.1 Create `gimnasioApp/services/onboarding.py` — `generate_temp_password()` using `secrets.token_urlsafe(12)`
- [x] 2.2 Add `provision_gym_from_demo(demo)` — atomic create Gimnasio + admin Usuario + link demo.gym_creado; raise ValidationError on duplicate email
- [x] 2.3 Add `revert_gym_from_demo(demo)` — soft-delete: gym.is_active=False, admin.is_active=False, demo.gym_creado=None
- [x] 2.4 Unit tests for onboarding.py — test temp password entropy/length, provision creates correct objects, revert soft-deletes, duplicate email raises
- [x] 2.5 Override `DemoRequestViewSet.perform_update` in `gimnasioApp/views.py` — detect pendiente→contactado, call provision, call revert on reverse, handle idempotency
- [x] 2.6 Add `email_sent` SerializerMethodField to `DemoRequestSerializer` in `gimnasioApp/serializers.py` + add `gym_creado` to read_only_fields
- [x] 2.7 Integration tests — PATCH pendiente→contactado creates gym+admin; idempotent re-PATCH; duplicate email→400; reverse→soft-delete; unauthenticated→401; non-superadmin→403

## Phase 3: Email Service + Templates

- [x] 3.1 Create `gimnasioApp/services/email.py` — `send_welcome_email(gym_id, admin_id, temp_password)` using `send_mail` with `EmailMultiAlternatives`
- [x] 3.2 Create `gimnasioApp/templates/emails/welcome_admin.html` — ControlFit branding, admin email, temp password, login link, must-change notice
- [x] 3.3 Create `gimnasioApp/templates/emails/welcome_admin.txt` — plain text fallback
- [x] 3.4 Add EMAIL config to `gimnasio/settings.py` — `EMAIL_BACKEND` (console dev, smtp prod), `DEFAULT_FROM_EMAIL`, `EMAIL_HOST*` env vars
- [x] 3.5 Wire `transaction.on_commit` in `perform_update` to call `send_welcome_email`; catch exceptions, log, set `email_sent=False`
- [x] 3.6 Tests — mock `send_mail`, verify subject/body/context; verify failure logs + `email_sent=False` in response

## Phase 4: Password Change Flow

- [x] 4.1 Create `gimnasioReact/src/pages/auth/PasswordChangeRequiredPage.tsx` — form with new password + confirm, validation, POST to `/auth/password/change/`
- [x] 4.2 Add `must_change_password?` to `AuthUser` in `gimnasioReact/src/model/dto/user.dto.ts`
- [x] 4.3 Update `AuthProvider.tsx` to expose `must_change_password` from profile response
- [x] 4.4 Update `ProtectRoute.tsx` to redirect to `/cambiar-password/` when `must_change_password` is true
- [x] 4.5 Add toast helpers in `gimnasioReact/src/utils/toast.ts` — `showSuccessToast`, `showErrorToast`, `showLoadingToast`

## Phase 5: Frontend Integration

- [x] 5.1 Add `gym_creado?` to `DemoRequest` type in `gimnasioReact/src/api/action/demoRequests.api.ts`
- [x] 5.2 Update `DemoRequestsPage.tsx` — `handleToggleEstado`: gym-aware toast when gym_creado present, loading badge during PATCH, error 400 toast for duplicate email
- [x] 5.3 RTL tests — toast success on gym created, loading state, error handling

## Phase 6: Verification & Polish

- [x] 6.1 E2E manual checklist — demo→contactado→gym+admin+email→login→password change
- [x] 6.2 Lint + typecheck — backend: ruff/mypy, frontend: eslint/tsc
- [x] 6.3 Full test suite green — `python manage.py test gimnasioApp` (163 tests) + `npm run build` (47 tests)

(End of file - total 73 lines)