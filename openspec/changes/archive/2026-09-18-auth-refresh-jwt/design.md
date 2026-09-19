# Design: auth-refresh-jwt

## Technical Approach

Complete the cookie-based JWT auth flow by subclassing SimpleJWT's stock views. Login sets an HttpOnly refresh cookie and returns only `{access}` in the body. Refresh reads the cookie, rotates the token, re-sets the cookie, and returns `{access}`. Logout blacklists the refresh token server-side and clears the cookie. A shared cookie helper eliminates duplication between the new views and the existing `RegisterViewSet`.

The frontend contract is preserved: `refreshAccessToken()` stays body-less POST to `/token/refresh/`, axios clients already use `withCredentials: true`. No frontend API shape changes required.

## Architecture Decisions

### Decision: SameSite=None + Secure (production) via shared helper

| Option | Tradeoff | Decision |
|--------|----------|----------|
| SameSite=None + Secure | Works cross-site (Vercel→Render); requires HTTPS (already true); slightly more permissive | **Chosen** |
| Same-origin proxy (vercel.json rewrites) | Keeps Lax; adds infra coupling; vercel.json currently SPA-only | Rejected — unnecessary complexity for this fix |

**Rationale**: Vercel frontend (`https://controlfit.vercel.app`) and Render API are different sites. `SameSite=Lax` will NOT send cookies cross-site in production — the fix would work locally and silently break in prod. The existing `AUTH_COOKIE_SECURE = not DEBUG` pattern already conditionals on environment. A shared helper reads `settings.DEBUG` to set `samesite='None'` (prod) or `samesite='Lax'` (dev), matching `secure=not settings.DEBUG`.

**Exact settings change**: The shared helper (`gimnasioApp/auth_cookie.py`) reads these values from `gimnasio/settings.py` SIMPLE_JWT block:
- `AUTH_COOKIE_SECURE = not DEBUG` (existing, line 231)
- `AUTH_COOKIE_SAMESITE = 'None' if not DEBUG else 'Lax'` (replaces hardcoded `'Lax'`)

**Manual prod test required (DoD)**: After deploy, verify on `controlfit.vercel.app` that login sets the cookie and session survives >30 min. Browser DevTools → Application → Cookies → confirm `refresh_token` has `SameSite=None`, `Secure`, `Path=/gym/api/v1/token/refresh/`.

### Decision: Shared auth cookie helper

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Shared helper (`auth_cookie.py`) | Single source of truth; RegisterViewSet + login + refresh + logout use same attrs | **Chosen** |
| Per-view duplication | Simpler but RegisterViewSet already duplicates; third copy in login would be worse | Rejected |
| Use SimpleJWT built-in cookie support | SimpleJWT 5.5.1 does NOT support cookie-based refresh natively; would require monkey-patching | Rejected |

**Rationale**: `RegisterViewSet` (views.py:128-136) already sets the cookie with the correct pattern. Adding two more custom views that duplicate the same 6 attributes invites drift. A helper function `set_refresh_cookie(response, token, request=None)` and `clear_refresh_cookie(response)` centralizes the logic.

### Decision: Custom TokenObtainPairView (login)

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Subclass `TokenObtainPairView` | Keeps SimpleJWT serializer + validation; override `post()` to set cookie + return only access | **Chosen** |
| Pure custom view (APIView) | Full control; duplicates credential validation logic | Rejected — unnecessary |

**Rationale**: Subclassing preserves SimpleJWT's `TokenObtainPairSerializer` (credential validation, `get_token()`, `update_last_login`). The override is minimal: call `super().post()`, extract refresh from response body, delete it from body, set cookie, return modified response.

### Decision: Custom TokenRefreshView (cookie-based refresh + rotation)

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Subclass `TokenRefreshView` with cookie read + rotation | Reads refresh from cookie, validates, rotates, re-sets cookie | **Chosen** |
| Custom APIView | Full control; duplicates token validation | Rejected |

**Rationale**: Subclassing keeps SimpleJWT's `TokenRefreshSerializer` (token validation, blacklist check). The override: read `request.COOKIES['refresh_token']`, inject into `request.data['refresh']`, call `super().post()`, on success extract new refresh from response, re-set cookie, return only `{access}`.

### Decision: Server-side logout endpoint

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Custom logout view (APIView, AllowAny) | Reads cookie → blacklist → clear cookie; independent of stock `TokenBlacklistView` | **Chosen** |
| Reuse stock `TokenBlacklistView` | Requires sending refresh in body; frontend would need to read HttpOnly cookie (impossible) | Rejected |

**Rationale**: Frontend `performLogout` (AuthProvider.tsx:81-96) currently tries `POST /token/blacklist/` with body `{refresh: getRefreshTokenFromCookie()}` — but `getRefreshTokenFromCookie()` always returns `null` for HttpOnly. The new endpoint reads the cookie server-side, blacklists, clears it. Frontend calls `POST /auth/logout/` (no body needed, or minimal body ignored).

### Decision: On-mount session restore

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Attempt cookie-based refresh on mount | New tabs restore session automatically; costs one API call on load | **Chosen** |
| Remove dead branch, don't restore | Simpler; new tabs always require re-login | Rejected — bad UX |

**Rationale**: `AuthProvider.initAuth` (AuthProvider.tsx:21-41) has an unreachable branch at L31-35 because `getRefreshTokenFromCookie()` always returns null (HttpOnly). With the cookie in place, this branch becomes reachable. The fix: attempt `POST /token/refresh/` (body-less) on mount. If it succeeds, store the new access token and load user profile. If it fails (cookie expired/missing), set `loading=false` and redirect to login.

## Data Flow

### Login
```
Frontend → POST /token/ (credentials)
  → Custom TokenObtainPairView
    → validate credentials via TokenObtainPairSerializer
    → generate refresh + access tokens
    → set refresh as HttpOnly cookie (SameSite=None+Secure in prod)
    → return {access} only
  ← 201 {access}
Frontend ← store access in sessionStorage
```

### Silent Refresh (20-min interval)
```
LayoutAdmin timer → refreshAccessToken()
  → POST /token/refresh/ (no body)
  → Custom TokenRefreshView
    → read refresh from request.COOKIES
    → validate + blacklist old (ROTATE_REFRESH_TOKENS=True)
    → generate new refresh
    → re-set cookie with new refresh
    → return {access}
  ← 200 {access}
Frontend ← update sessionStorage
```

### Proactive Refresh (<5 min to expiry)
```
axiosPrivate request interceptor → isTokenExpiringSoon()
  → refreshAccessToken() (same flow as silent refresh)
```

### Reactive 401 Refresh
```
axiosPrivate response interceptor → 401
  → refreshAccessToken() (same flow as silent refresh)
  → retry original request
  → on failure → clear tokens + redirect /login
```

### Logout
```
Frontend → POST /auth/logout/ (no body needed)
  → Custom LogoutView
    → read refresh from cookie
    → blacklist via RefreshToken(token).blacklist()
    → clear cookie (Max-Age=0)
    → 200 {detail: "Logged out"}
  ← 200
Frontend ← clearAccessToken() + clearRefreshCookie() + navigate /login
```

### On-Mount Session Restore
```
AuthProvider.initAuth()
  → getAccessToken() from sessionStorage (per-tab)
  → if no access token:
    → POST /token/refresh/ (body-less, sends cookie)
    → if success: store new access, load profile
    → if 401: setLoading(false), redirect /login
  → if access token exists: load profile normally
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `gimnasioApp/auth_cookie.py` | Create | Shared `set_refresh_cookie(response, refresh_token)` and `clear_refresh_cookie(response)` helpers. Reads `AUTH_COOKIE_*` from settings. |
| `gimnasioApp/views.py` | Modify | Add 3 new views: `CookieTokenObtainPairView`, `CookieTokenRefreshView`, `LogoutView`. Update `RegisterViewSet` to use shared helper. |
| `gimnasioApp/urls.py` | Modify | Swap stock views (L36-38) with custom views. Add logout path. |
| `gimnasio/settings.py` | Modify | `ROTATE_REFRESH_TOKENS=True` (L218). Remove duplicate `CORS_ALLOWED_ORIGINS` at L194 (keep L239-243). Update `AUTH_COOKIE_SAMESITE` to conditional. |
| `gimnasioApp/tests.py` | Modify | Add `AuthCookieLoginTest`, `AuthCookieRefreshTest`, `AuthCookieLogoutTest` classes. |
| `gimnasioReact/src/utils/authStorage.ts` | Modify | Remove dead `getRefreshTokenFromCookie` (line 16-19) — no longer needed. `clearRefreshCookie` path is correct. |
| `gimnasioReact/src/context/AuthProvider.tsx` | Modify | Fix `initAuth` to attempt cookie refresh on mount. Fix `performLogout` to call new `/auth/logout/` endpoint (no body). Remove `getRefreshTokenFromCookie` import. |
| `gimnasioReact/src/api/users/users.api.ts` | Modify | Line 1: remove duplicate `axiosPublic` import from `axios.private.ts`; use `axiosPublic` from `axios.public.ts` (with `withCredentials`). |
| `gimnasioReact/src/model/dto/user.dto.ts` | No change | `LoginResponse` already has `access` only. `BlacklistRequest` becomes unused (keep for now). |

## Interfaces / Contracts

### Backend — New Views

```python
# gimnasioApp/views.py (new views, sketch)

class CookieTokenObtainPairView(TokenObtainPairView):
    """Login: set refresh as HttpOnly cookie, return access only."""
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            refresh = response.data.get('refresh')
            set_refresh_cookie(response, refresh)
            del response.data['refresh']  # return only {access}
        return response

class CookieTokenRefreshView(TokenRefreshView):
    """Refresh: read cookie, rotate, re-set cookie, return access only."""
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({'detail': 'No refresh token'}, status=401)
        request.data['refresh'] = refresh_token
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            new_refresh = response.data.get('refresh')  # rotated token
            if new_refresh:
                set_refresh_cookie(response, new_refresh)
                del response.data['refresh']
        return response

class LogoutView(APIView):
    """Logout: blacklist refresh + clear cookie."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            try:
                from rest_framework_simplejwt.tokens import RefreshToken
                RefreshToken(refresh_token).blacklist()
            except Exception:
                pass  # log but don't fail
        response = Response({'detail': 'Logged out'})
        clear_refresh_cookie(response)
        return response
```

### Backend — Shared Helper

```python
# gimnasioApp/auth_cookie.py (new file)

from django.conf import settings

def set_refresh_cookie(response, refresh_token):
    """Set the refresh token as an HttpOnly cookie."""
    cookie_settings = {
        'key': 'refresh_token',
        'value': str(refresh_token),
        'max_age': 604800,  # 7 days
        'httponly': True,
        'secure': not settings.DEBUG,
        'samesite': 'None' if not settings.DEBUG else 'Lax',
        'path': '/gym/api/v1/token/refresh/',
    }
    response.set_cookie(**cookie_settings)

def clear_refresh_cookie(response):
    """Clear the refresh token cookie."""
    response.delete_cookie(
        key='refresh_token',
        path='/gym/api/v1/token/refresh/',
    )
```

### Frontend — AuthProvider Init Fix

```typescript
// AuthProvider.tsx initAuth — updated logic
const initAuth = async () => {
  const token = getAccessToken();
  
  if (token) {
    setIsAuthenticated(true);
    await loadUser();
    return;
  }
  
  // No access token in sessionStorage — try cookie-based refresh
  try {
    const newToken = await refreshAccessToken();  // body-less POST, sends cookie
    setAccessToken(newToken);
    setIsAuthenticated(true);
    await loadUser();
  } catch {
    setLoading(false);  // cookie expired or missing → show login
  }
};
```

### Frontend — Logout Fix

```typescript
// AuthProvider.tsx performLogout — updated
const performLogout = useCallback(async () => {
  try {
    await axios.post(`${baseURL}/auth/logout/`, {}, { withCredentials: true });
  } catch {
    // Ignore — server may be down, still clear locally
  }
  clearAccessToken();
  clearRefreshCookie();
  setUser(null);
  setIsAuthenticated(false);
}, []);
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `set_refresh_cookie` sets correct attrs | Direct helper call + response cookie assertion |
| Unit | `clear_refresh_cookie` removes cookie | Direct helper call + response cookie assertion |
| Integration | Login sets HttpOnly cookie with correct attributes | `APIRequestFactory` → `CookieTokenObtainPairView.post()` → assert `response.cookies['refresh_token']` httponly, samesite, path, max_age |
| Integration | Refresh from cookie returns access + rotates | Login → extract cookie → set on refresh request → assert new access in body, old refresh blacklisted |
| Integration | Refresh with no cookie → 401 | `CookieTokenRefreshView.post()` with empty COOKIES → 401 |
| Integration | Logout blacklists + clears cookie | Login → logout → assert cookie cleared, old refresh blacklisted (reuse → 401) |
| Integration | Register still works (uses same helper) | Existing register flow → assert cookie set correctly |
| Regression | `python manage.py test gimnasioApp` green | Full test suite passes |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Migration / Rollout

No data migration required. Custom views are additive — they replace stock SimpleJWT views in urls.py. The change is backwards-compatible: existing sessions (if any) continue to work since the cookie path and key are unchanged.

Rollback: `git revert` restores stock SimpleJWT views + `ROTATE_REFRESH_TOKENS=False`. No database changes.

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| SameSite=None breaks in non-HTTPS dev environments | Low | Medium | Helper conditionally sets Lax in DEBUG; development typically same-origin (localhost:5173→localhost:8000) |
| Rotation race across tabs (two tabs refresh → blacklist each other) | Medium | Low | ACCEPTED per product decision; 401 path already redirects to login; per-tab queue stays |
| Cookie not sent in prod (same-site enforcement) | High (without fix) | High | SameSite=None+Secure + manual prod test in DoD |
| GimnasioMiddleware double-auth on token endpoints | Low | Low | New views stay AllowAny; middleware only activates for authenticated users or Bearer headers |
| Vestigial AUTH_COOKIE_* settings confuse maintainers | Low | Low | Shared helper reads from settings; vestigial block can be cleaned up in this change |
| Duplicate CORS_ALLOWED_ORIGINS (L194 vs L239) | Low | Low | Remove L194 definition; keep L239-243 with credentials + expose headers |
| Logout blacklist failure (DB error, invalid token) | Low | Low | Try/except in logout view; log error; still clear cookie |
| Frontend `axiosPublic` in `axios.private.ts` lacks `withCredentials` | Medium | Medium | Fix `users.api.ts` import to use correct `axiosPublic` from `axios.public.ts` |

## Open Questions

None — all decisions resolved. SameSite=None+Secure chosen with explicit reasoning and prod test requirement.
