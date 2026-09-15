# Design: JWT Refresh Hardening

## Technical Approach

Harden JWT authentication through incremental rollout: reduce token lifetimes, add double-submit CSRF protection, create a lightweight verify endpoint, and integrate with frontend via axios interceptors. The approach follows a 5-phase rollout to minimize breaking changes.

## Architecture Decisions

### Decision: CSRF Validation Strategy

**Choice**: View-level validation via reusable function `validate_csrf(request)` called from mutating views.

**Alternatives considered**:
1. Django middleware — intercepts ALL requests including login/refresh/logout which need to be exempt
2. DRF permission class — couples CSRF to authentication, complicates the existing permission stack
3. Decorator — requires manual application to each view, easy to forget

**Rationale**: A reusable function provides explicit control over which views enforce CSRF. It avoids middleware exemption lists and keeps the existing permission stack clean. The function can be called from viewsets, APIViews, or mixins with minimal boilerplate.

### Decision: CSRF Cookie Attributes

**Choice**: 
- `HttpOnly=false` (JavaScript-readable)
- `SameSite=Lax` in development, `SameSite=None + Secure` in production
- `Path=/gym/api/v1/` (matches refresh cookie path)
- `Max-Age=86400` (1 day, shorter than refresh token)

**Alternatives considered**:
1. HttpOnly=true — blocks JavaScript access, breaking double-submit pattern
2. SameSite=Strict — too restrictive for cross-origin API calls
3. Path=/ — leaks to non-API routes

**Rationale**: Double-submit pattern requires JavaScript access to the cookie value. SameSite=None in production enables cross-origin requests from Vercel frontend. Path scoping prevents cookie leakage to non-API routes.

### Decision: CSRF Enforcement Scope

**Choice**: All mutating endpoints (POST/PUT/PATCH/DELETE) under `/gym/api/v1/` except:
- `/token/` (login)
- `/token/refresh/` (refresh)
- `/auth/logout/` (logout)
- `/token/verify/` (verify)
- `/register/` (public registration)

**Alternatives considered**:
1. All endpoints including GET — breaks read-only operations
2. Only POST — misses PUT/PATCH/DELETE mutations
3. Whitelist approach — requires maintaining exemption list

**Rationale**: Exemptions are necessary because login/refresh/logout set/clear cookies and cannot provide CSRF tokens. Verify is read-only. Registration is public. The blacklist approach (exempt specific paths) is more maintainable than whitelisting all protected paths.

### Decision: Feature Flag for CSRF Enforcement

**Choice**: `settings.CSRF_ENFORCE = False` initially, with log-only validation.

**Alternatives considered**:
1. Immediate enforcement — risks breaking existing clients
2. No flag — no gradual rollout possible
3. Per-endpoint flags — too granular, adds complexity

**Rationale**: A single boolean flag enables gradual rollout. Log-only mode (Phase 2) validates the implementation without breaking existing clients. The flag is checked in `validate_csrf()` to allow clean toggling.

## Data Flow

### Login Flow

```
Client → POST /gym/api/v1/token/ (credentials)
Server → Validate credentials → Generate access + refresh tokens
Server → Set refresh cookie (HttpOnly) + CSRF cookie (JS-readable)
Server → Return access token only (no refresh in body)
```

### Refresh Flow

```
Client → POST /gym/api/v1/token/refresh/ (refresh cookie)
Server → Read refresh from cookie → Validate → Rotate tokens
Server → Set new refresh cookie + new CSRF cookie
Server → Return new access token
```

### Mutating Request Flow

```
Client → Read CSRF cookie → Add X-CSRF-Token header
Client → POST/PUT/PATCH/DELETE /gym/api/v1/... (access header + CSRF header)
Server → Validate CSRF header matches cookie → Process request
Server → Return 200 or 403 (CSRF_MISMATCH)
```

### Verify Flow

```
Client → GET /gym/api/v1/token/verify/ (access header)
Server → Validate access token → Return {valid: true, exp: timestamp} or 401
```

### Logout Flow

```
Client → POST /gym/api/v1/auth/logout/ (refresh cookie)
Server → Blacklist refresh token → Clear refresh + CSRF cookies
Server → Return 200
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `gimnasio/settings.py` | Modify | Update SIMPLE_JWT lifetimes, add CSRF_ENFORCE flag |
| `gimnasioApp/auth_cookie.py` | Modify | Add CSRF cookie helpers (set/clear/read) |
| `gimnasioApp/views.py` | Modify | Add CookieTokenVerifyView, CSRF validation |
| `gimnasioApp/urls.py` | Modify | Add /token/verify/ endpoint |
| `gimnasioReact/src/api/axios/axios.private.ts` | Modify | Add CSRF header interceptor |
| `gimnasioReact/src/api/axios/refreshToken.api.ts` | Modify | Add verifyToken function |

## Interfaces / Contracts

### Backend

```python
# settings.py additions
SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(minutes=15)  # was 30
SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'] = timedelta(days=3)     # was 7

CSRF_ENFORCE = False  # Feature flag for gradual rollout

# auth_cookie.py new helpers
def set_csrf_cookie(response, token): ...
def clear_csrf_cookie(response): ...
def get_csrf_token(request): ...

# views.py new view
class CookieTokenVerifyView(APIView):
    permission_classes = [AllowAny]
    def get(self, request): ...
    
# CSRF validation function
def validate_csrf(request): ...  # Returns True/False, logs violations
```

### Frontend

```typescript
// axios.private.ts additions
axiosPrivate.interceptors.request.use((config) => {
  // Read CSRF cookie, add X-CSRF-Token header for mutating requests
  if (['post', 'put', 'patch', 'delete'].includes(config.method)) {
    config.headers['X-CSRF-Token'] = getCsrfCookie('csrftoken');
  }
  return config;
});

// refreshToken.api.ts additions
export const verifyToken = async (): Promise<{valid: boolean, exp?: number}> => {
  const { data } = await axiosPrivate.get('/token/verify/');
  return data;
};
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Cookie helpers (set/clear/read) | Mock response object, verify cookie attributes |
| Unit | CSRF validation function | Mock request with/without header, verify behavior |
| Unit | CookieTokenVerifyView | Mock JWT tokens, verify response schema |
| Integration | Login flow | Full request cycle, verify cookies set correctly |
| Integration | Refresh flow | Full request cycle, verify token rotation |
| Integration | CSRF validation | Mutating requests with/without header |
| Frontend | Axios interceptor | Mock cookies, verify header injection |
| Frontend | Verify call | Mock API response, verify redirect on invalid |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Migration / Rollout

### Phase 1: Config Only
- Update SIMPLE_JWT lifetimes in settings.py
- No code changes, just configuration
- Existing tokens honor original expiry

### Phase 2: CSRF Cookie Set + Log-Only
- Add CSRF cookie helpers to auth_cookie.py
- Set CSRF cookie on login/refresh/logout
- Add validate_csrf() with log-only mode (CSRF_ENFORCE=False)
- No enforcement, just logging violations

### Phase 3: Verify Endpoint
- Add CookieTokenVerifyView to views.py
- Add /token/verify/ to urls.py
- No frontend integration yet

### Phase 4: Frontend Integration
- Add CSRF header interceptor to axios.private.ts
- Add verifyToken() to refreshToken.api.ts
- Add verify call on app mount
- Remove silent refresh interval (20min → verify-based)

### Phase 5: Enforce CSRF
- Set CSRF_ENFORCE=True in settings.py
- CSRF validation now returns 403 on missing/invalid header
- Remove startSilentRefresh from frontend

## Open Questions

- [ ] Should CSRF token be regenerated on each request or fixed per session?
- [ ] Should we add rate limiting to verify endpoint to prevent abuse?
- [ ] How to handle CSRF cookie expiration (1 day) vs refresh token (3 days)?
