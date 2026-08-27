# Proposal: Auto-create Gym from Demo Request

## Intent
When a SuperAdmin marks a `DemoRequest` as `contactado`, automatically provision the lead's `Gimnasio` + an `admin` `Usuario` (temp password) and email the credentials. Removes the manual two-step and speeds B2B onboarding.

## Scope
### In Scope
- Migration: `DemoRequest.gym_creado` FK (nullable, SET_NULL).
- `DemoRequestViewSet.perform_update`: atomic create Gimnasio + admin Usuario + link.
- `services/email.py`: `send_welcome_email` + HTML template; `EMAIL_BACKEND` config.
- Frontend: success toast on gym creation, no redirect; forward-only badge.
- Integration tests (happy / idempotent / dup-email / email-fail).

### Out of Scope
- Manual "create gym" form (already exists at platform).
- WhatsApp / Celery worker in v1.
- Forced password-change flow (depends on existing reset feature).

## Capabilities
### New
- `demo-gym-onboarding`: backend atomic provisioning + idempotency on `pendiente→contactado`.
- `welcome-email`: email service + template.
- `demo-requests-ui`: frontend behavior change (toast, no nav, forward-only badge).
### Modified
- None (no existing spec for demo requests).

## Approach
- Add nullable `gym_creado` FK to `DemoRequest` (`gimnasioApp/models.py`); new migration.
- Override `DemoRequestViewSet.perform_update` (views.py ~868): wrap gym+user+link in `@transaction.atomic`, only when `pendiente→contactado` and `gym_creado is None`. After `super().perform_update` commits, call `send_welcome_email(...)` (sync, post-commit, try/except) → set `email_sent` in response.
- `send_welcome_email(gym, usuario, password_temp)` via `EmailMultiAlternatives`; temp pw = `secrets.token_urlsafe(12)`, hashed via `make_password`.
- `DemoRequestSerializer` (`fields='__all__'`) already exposes `gym_creado`; add read-only `email_sent`.
- Frontend: add `gym_creado?` to `DemoRequest` type; `handleToggleEstado` shows success toast when `updated.gym_creado` truthy; badge toggles only forward.

## Affected Areas
| Area | Impact | Description |
| `gimnasioApp/models.py` | Modified | add `gym_creado` FK + migration |
| `gimnasioApp/views.py` | Modified | `DemoRequestViewSet.perform_update` |
| `gimnasioApp/serializers.py` | Modified | add `email_sent` read-only |
| `gimnasioApp/services/email.py` | New | `send_welcome_email` + template |
| `gimnasio/settings.py` | Modified | EMAIL_BACKEND (console dev / SMTP prod) |
| `gimnasioApp/tests.py` | Modified | integration tests |
| `gimnasioReact/.../DemoRequestsPage.tsx` | Modified | toast, no nav, forward-only |
| `gimnasioReact/.../demoRequests.api.ts` | Modified | `gym_creado?` in type |

## Business Rules
- Only `pendiente→contactado` triggers creation; reverse not supported via UI.
- Idempotent: if `gym_creado` set, skip creation (no duplicate gym/user).
- Temp password strong (token_urlsafe 12); sent once via email; never persisted plaintext.
- `Usuario.email` unique → duplicate → catch IntegrityError → 400 clear message.

## Edge Cases
- Lead email already a Usuario → 400 (policy TBD, Q5).
- `nombre_gimnasio` > 50 chars overflows `lastname` max 50 (Q4).
- `telefono` > 20 overflows `Gimnasio.phone` max 20; validate/truncate.
- Email fails post-commit → gym stays, `email_sent=False`, UI warns + retry path.

## Risks
| Risk | Likelihood | Mitigation |
| No email infra (no SMTP/Celery) | High | configure EMAIL_BACKEND; console dev; sync send post-commit |
| Temp password in plaintext email | Med | strong random pw + force reset in app |
| Slow SMTP blocks request | Med | send after commit; timeouts; non-blocking |
| Migration on demo_request | Low | additive nullable FK, reversible |

## Rollback Plan
- `migrate gimnasioApp <prev>` removes FK column. Revert `perform_update` override (no auto-create). Email config back to no-op. Created gyms optionally `is_active=False`.

## Dependencies
- SMTP credentials / `EMAIL_BACKEND` for prod. No Celery → sync send in v1.

## Success Criteria
- [ ] PATCH `pendiente→contactado` atomically creates Gimnasio + admin Usuario, links `gym_creado`.
- [ ] Idempotent re-PATCH: no duplicate.
- [ ] Welcome email sent (or `email_sent=False` surfaced to UI).
- [ ] Frontend: success toast, no redirect, reverse toggle disabled.
- [ ] Integration tests pass (`python manage.py test gimnasioApp`).

## Questions for Clarification (proposal round)
1. **Email transport:** sync send (recommended, low volume) vs add Celery+Redis worker (async)? No worker exists today.
2. **Reverse/undo:** if wrongly marked contactado, allow revert to pendiente (orphans gym) or irreversible (gym stays)?
3. **Forced reset:** does the app force temp-password change on first login? If not, temp pw stays valid.
4. **Admin profile:** `lastname` max 50; gym name may exceed. Populate `name='Admin'`, `lastname=` truncated gym name?
5. **Duplicate email:** lead email already a Usuario → block 400, or link existing user to new gym?
