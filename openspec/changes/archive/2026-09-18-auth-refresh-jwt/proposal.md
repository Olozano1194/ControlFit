# Proposal: Cookie-Based JWT Auth Flow (login → refresh → logout)

## Intent

JWT refresh is broken after normal login. The stock `TokenObtainPairView` returns `access`+`refresh` in the JSON body and sets **no cookie**, while the frontend contract is cookie-based: `refreshAccessToken()` posts to `/token/refresh/` with **no body** and every relevant axios client runs `withCredentials: true`. The stock `TokenRefreshView` reads refresh from the **body**, so every refresh attempt fails after login and the user is logged out at ~30 min (access expiry). The codebase already scaffolds the intended cookie design (`RegisterViewSet` sets the HttpOnly refresh cookie; `AUTH_COOKIE_*` settings exist but are vestigial) — this change completes it.

## Problem Statement

- Login (`gimnasioApp/urls.py:36`) returns tokens in body, discards the refresh client-side (`authUser.api.ts:11` keeps only `data.access`); nothing usable remains after login.
- Refresh (`/token/refresh/`, body-less by contract) 400s against stock `TokenRefreshView` — silent 20-min timer, proactive <5min, and reactive 401 retry all fail.
- Logout never blacklists server-side: `getRefreshTokenFromCookie()` always returns null for HttpOnly → `POST /token/blacklist/` is always skipped; refresh tokens stay valid 7 days.
- `ROTATE_REFRESH_TOKENS=False` in settings; duplicate `axiosPublic` (users.api.ts one lacks `withCredentials`) would silently drop Set-Cookie on register.
- ZERO auth tests exist (`gimnasioApp/tests.py`, 1917 lines — no login/refresh/blacklist/cookie coverage).

## Business Value

Staff (admin/recepción) sessions currently hard-expire at 30 min with no renewal path — users get thrown to `/login` mid-work. Fixing refresh restores continuous staff sessions; server-side logout closes the gap where logged-out tokens remain valid for 7 days.

## Scope

### In Scope
1. Custom `TokenObtainPairView` (login): set refresh as HttpOnly cookie mirroring `RegisterViewSet` (L128-136); access in body only.
2. Custom `TokenRefreshView`: read refresh from **cookie** (not body), rotate it, re-set the cookie, return access.
3. Server-side logout endpoint: read refresh cookie → blacklist → clear cookie.
4. Settings: `ROTATE_REFRESH_TOKENS=True` (`BLACKLIST_AFTER_ROTATION` already True); SameSite conditional (see Open Decision); remove duplicate `CORS_ALLOWED_ORIGINS` (L194 vs L239); wire `AUTH_COOKIE_*` into the custom views or delete the vestigial block.
5. Fix duplicate `axiosPublic`: `users.api.ts` must use the `withCredentials` instance.
6. Auth tests: login→refresh→logout end-to-end with cookie assertions (attrs, rotation, blacklist reuse, invalid cookie → 401).

### Out of Scope
- **Public registration**: no register endpoint changes, no register UI wiring (STAFF ONLY — admin/recepción).
- Session lifetime changes: access 30 min / refresh 7 days **kept**.
- Multi-tab sync: no BroadcastChannel/tab coordination; rotation stays simple.
- SameSite production choice: **not decided here** — flagged for design phase.

## Capabilities

### New Capabilities
- `auth`: cookie-based JWT login, refresh-with-rotation, and server-side logout for staff users (no auth spec exists in `openspec/specs/` today).

### Modified Capabilities
- None.

## Approach

Complete the cookie-based flow (exploration Approach 1, confirmed as the only direction consistent with the frontend contract):
1. Subclass `TokenObtainPairView` → on successful login, set `refresh_token` HttpOnly cookie (same attrs as `RegisterViewSet`: `path=/gym/api/v1/token/refresh/`, `max_age=604800`, `httponly`, `secure=not DEBUG`, SameSite per env) and return `{access}` only.
2. Subclass `TokenRefreshView` → read refresh from cookie, validate, rotate (`ROTATE_REFRESH_TOKENS=True`), re-set cookie, return `{access}`.
3. New logout view → read cookie, blacklist token, clear cookie (both cookie paths/values).
4. Swap stock views in `gimnasioApp/urls.py:36-38`; keep `/token/blacklist/` or replace with the logout endpoint.
5. Frontend: preserve the body-less contract (`refreshToken.api.ts`, `authUser.api.ts` unchanged); fix `users.api.ts` axiosPublic; remove dead `getRefreshTokenFromCookie` / unreachable `initAuth` restore branch (or add a real on-mount refresh attempt — design decides).
6. Tests: new auth test classes in `gimnasioApp/tests.py`.

## Key Decisions & Assumptions

| Decision | Choice |
|----------|--------|
| Session lifetime | KEEP: access 30 min, refresh 7 days (user-confirmed) |
| Multi-tab rotation | Simple rotation; occasional spurious logout in a second tab ACCEPTED; no BroadcastChannel (user-confirmed) |
| Logout | Server-side invalidation — endpoint blacklists refresh + clears cookie, not just cookie clearing (user-confirmed) |
| Users | STAFF ONLY (admin/recepcion); public registration OUT OF SCOPE (user-confirmed) |
| Frontend contract | Body-less refresh preserved; no API shape changes |
| Cookie attrs | Mirror `RegisterViewSet` pattern (path `/gym/api/v1/token/refresh/`, 7d, HttpOnly, secure=not DEBUG) |
| AllowAny | New token endpoints MUST stay AllowAny (`GimnasioMiddleware` constraint) |

## Open Decision (design phase decides — do NOT decide in proposal)

**Production SameSite**: frontend (https://controlfit.vercel.app) and API (Render) are different sites → `SameSite=Lax` cookies are NOT sent cross-site.
- Option A: `SameSite=None` + `Secure` in prod (works cross-site; needs HTTPS everywhere — already true; `AUTH_COOKIE_DOMAIN=None` host-only cookie stays correct for direct-to-Render calls). **Default recommendation.**
- Option B: same-origin proxy (`vercel.json` rewrites `/gym/api/v1/*` → Render; `vercel.json` currently only rewrites to index.html) — keeps Lax, adds infra coupling + env change; not required for the core fix.

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| SameSite cross-site breakage in prod (fix works locally, fails on Vercel→Render) | High | Explicit design decision (None+Secure default); manual cross-site test in DoD |
| Rotation race across tabs (two tabs refresh → blacklist each other) | Med | ACCEPTED per product decision; per-tab queue stays; 401 path already redirects to login |
| Session-restore illusion (new tab always logged out; HttpOnly invisible to JS) | High (UX) | Design decides on-mount refresh attempt; at minimum remove dead `initAuth` branch |
| Logout no-op today (tokens valid 7d post-logout) | High | New server-side logout endpoint blacklists + clears |
| Access token in sessionStorage (per-tab, lost on new tab) | Med | Accepted, existing behavior; documented in specs |
| Duplicate axiosPublic drops Set-Cookie (register) | Low | Fix `users.api.ts` import (deliverable) |
| Vestigial config confusion (`AUTH_COOKIE_*`, duplicate CORS) | Low | Wire or delete during this change |
| `GimnasioMiddleware` double auth on token endpoints | Low | Keep endpoints AllowAny; anonymous-refresh tests |

## Rollback Plan

`git revert` the feature commit. Custom views are additive — revert restores stock SimpleJWT views + `ROTATE_REFRESH_TOKENS=False`. No data migration involved. If SameSite=None shipped, revert restores Lax.

## Dependencies

- None external. SimpleJWT 5.5.1 + `rest_framework_simplejwt.token_blacklist` already installed (settings.py:57).
- Prod validation requires Vercel env (`VITE_API_URL_PROD` real value) + Render deploy for the cross-site manual test.

## Success Criteria (Definition of Done)

- [ ] `POST /gym/api/v1/token/` sets HttpOnly `refresh_token` cookie with correct attrs; body contains `access` only
- [ ] `POST /gym/api/v1/token/refresh/` (body-less) reads cookie, returns new access, rotates + re-sets cookie; reuse of the old refresh → 401
- [ ] Logout endpoint blacklists the refresh token + clears the cookie; subsequent refresh → 401
- [ ] `python manage.py test gimnasioApp` green (new auth tests + existing suite)
- [ ] Silent (20-min), proactive (<5-min), and reactive (401) refresh work in dev (same-site)
- [ ] Manual prod test on controlfit.vercel.app: login, session survives > 30 min (cross-site cookie verified)

## Impact Surface

| Area | Impact | Description |
|------|--------|-------------|
| `gimnasioApp/views.py` | Modified | +3 views: cookie TokenObtainPairView, cookie TokenRefreshView, logout view |
| `gimnasioApp/urls.py` | Modified | Swap stock views (L36-38); add logout path |
| `gimnasio/settings.py` | Modified | `ROTATE_REFRESH_TOKENS=True`; SameSite conditional; CORS duplicate cleanup; `AUTH_COOKIE_*` wiring/removal |
| `gimnasioApp/tests.py` | Modified | +auth test classes (login/refresh/logout/cookies/rotation) |
| `gimnasioReact/src/api/users/users.api.ts` | Modified | Use `withCredentials` axiosPublic |
| `gimnasioReact/src/utils/authStorage.ts` | Modified | Remove/rework dead `getRefreshTokenFromCookie`; align `clearRefreshCookie` |
| `gimnasioReact/src/context/AuthProvider.tsx` | Modified | `initAuth` dead branch; server-side logout call (design decides on-mount restore) |
| `gimnasioReact/src/api/axios/refreshToken.api.ts`, `authUser.api.ts`, `axios.public.ts` | Unchanged | Contract preserved |

## Non-Goals

- No refresh-token exposure to JS (stays HttpOnly).
- No public registration, password reset, or account lifecycle work.
- No cross-tab session sync, no token-in-localStorage migration.
- No changes to `LayoutAdmin` silent-refresh wiring.
