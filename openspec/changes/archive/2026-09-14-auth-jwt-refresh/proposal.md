# SDD Change Proposal: auth-jwt-refresh

## Intent

Harden JWT authentication by reducing token exposure window, adding explicit CSRF protection beyond SameSite, and providing a lightweight token verification endpoint for silent frontend validation.

## Scope

### In Scope

1. **Token lifetime reduction**
   - Access token: 30 min → 15 min
   - Refresh token: 7 days → 3 days

2. **Explicit CSRF protection (double-submit cookie)**
   - Set CSRF cookie on login/refresh (HttpOnly=false, SameSite=Lax/None, Secure in prod)
   - Require `X-CSRF-Token` header on all mutating requests (POST, PUT, PATCH, DELETE)
   - Validate CSRF token matches cookie value

3. **Token introspection endpoint**
   - New `GET /token/verify/` endpoint
   - Returns `{ valid: true, exp: timestamp }` or 401
   - No token rotation, no cookie changes — read-only validation

4. **Frontend integration**
   - axiosPrivate interceptor: read CSRF cookie → send `X-CSRF-Token` header
   - On app mount: call `/token/verify/` for silent session validation
   - Adjust/remove aggressive silent refresh interval (20 min → verify-based)

### Out of Scope

- Multi-device session management (list/revoke active sessions)
- Device trust/fingerprinting (remember trusted devices, alert on suspicious login)
- Logout everywhere (revoke all refresh tokens for a user)
- Refresh token rotation policy changes (keep `ROTATE_REFRESH_TOKENS=True`, `BLACKLIST_AFTER_ROTATION=True`)

## Current State

- **Backend**: Django 5.1 + DRF + SimpleJWT
  - `SIMPLE_JWT`: access=30min, refresh=7d, rotation+blacklist enabled
  - Endpoints: `/token/` (login), `/token/refresh/`, `/auth/logout/`
  - Refresh token in HttpOnly cookie (`/gym/api/v1/` path)
  - No CSRF cookie, no verify endpoint

- **Frontend**: React + axios
  - `axiosPrivate` with proactive refresh (5min margin), 401 auto-refresh queue, silent refresh every 20min
  - Access token in `sessionStorage`, refresh in HttpOnly cookie
  - No CSRF header, no token verify call

## Approach

Incremental rollout to minimize breaking changes:

1. **Phase 1 — Config**: Deploy SIMPLE_JWT lifetime changes. New tokens get new lifetimes; existing tokens honour original expiry.
2. **Phase 2 — CSRF cookie**: Set CSRF cookie on login/refresh (no validation yet, log-only mode).
3. **Phase 3 — Verify endpoint**: Deploy `CookieTokenVerifyView` at `/token/verify/`.
4. **Phase 4 — Frontend**: Add CSRF header interceptor + `/token/verify/` call on app mount.
5. **Phase 5 — Enforce**: Enable CSRF validation on mutating endpoints. Remove old silent refresh interval.

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Existing access tokens still valid 30min after deploy | High | Low | Acceptable; natural expiry |
| Existing refresh tokens still valid 7d after deploy | High | Low | Acceptable; natural expiry |
| Frontend/backend CSRF mismatch during rollout | Medium | High | Log-only mode first; feature flag validation |
| CSRF cookie path misalignment | Low | High | Explicit `/gym/api/v1/` path in both set/validate |
| Silent verify fails on slow network | Medium | Medium | Fallback to proactive refresh; graceful degradation |
| Subdomain cookie leakage (SameSite=None) | Low | Medium | CSRF double-submit adds second factor |

## Assumptions

- 15 min access / 3 day refresh acceptable UX for gym management (staff use, not public consumer)
- Double-submit CSRF (cookie + header) preferred over SameSite-only for subdomain protection
- `/token/verify/` returns `200 { valid: true, exp: <unix_ts> }` or `401 { valid: false }`
- Silent verify on app load replaces/reduces need for aggressive silent refresh interval
- No changes to `AUTH_USER_MODEL`, multi-tenant middleware, or permission classes

## Migration Strategy

1. Deploy backend config (lifetimes) → new tokens shorter, old tokens expiry unchanged
2. Deploy CSRF cookie setting (login/refresh) + optional validation middleware (log violations only)
3. Deploy verify endpoint
4. Deploy frontend with CSRF header + verify-on-mount
5. Enable CSRF enforcement (return 403 on missing/invalid header)
6. Remove `startSilentRefresh` / 20min interval from frontend

## Success Criteria

- All existing tests pass (`python manage.py test gimnasioApp`)
- New tests cover: verify endpoint, CSRF validation, lifetime config
- Frontend loads without 401 storm; silent verify works
- Mutating requests without CSRF header → 403
- No regression in login/refresh/logout flows