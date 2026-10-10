# Auth Flow: Django (HttpOnly Cookie JWT) + React

## Sequence Diagram

```mermaid
sequenceDiagram
    participant U as Usuario
    participant R as React (Vite/Prod)
    participant D as Django API

    Note over U,D: LOGIN
    U->>R: Ingresa email/password
    R->>D: POST /api/auth/login/ {email, password}
    D->>D: Valida credenciales
    D->>D: Genera access (15min) + refresh (7d)
    D->>R: 200 OK {user} + Set-Cookie: access=...; HttpOnly; Secure; SameSite=Lax<br/>Set-Cookie: refresh=...; HttpOnly; Secure; SameSite=Lax
    R->>U: Redirige a /dashboard

    Note over U,D: PRIMER REQUEST AUTENTICADO
    U->>R: Navega a /dashboard
    R->>D: GET /api/members/ (Cookie: access=...)
    D->>D: Valida access token desde cookie
    D->>R: 200 OK {members}

    Note over U,D: AUTO-REFRESH (access expirado)
    U->>R: Acción que requiere API
    R->>D: GET /api/members/ (Cookie: access=expired)
    D->>R: 401 Unauthorized
    R->>D: POST /api/auth/refresh/ (Cookie: refresh=...)
    D->>D: Valida refresh, rota (blacklist old, issue new)
    D->>R: 200 OK {access} + Set-Cookie: access=new; HttpOnly...
    R->>D: Reintenta GET /api/members/ (Cookie: access=new)
    D->>R: 200 OK {members}

    Note over U,D: CSRF PROTECTION
    R->>D: GET /api/auth/csrf/ (al inicio app)
    D->>R: 200 {csrfToken: "abc123"}
    R->>R: Guarda en memoria
    R->>D: POST /api/payments/ (Header: X-CSRFToken: abc123)
    D->>D: Valida CSRF token
    D->>R: 201 Created

    Note over U,D: LOGOUT
    U->>R: Click "Cerrar sesión"
    R->>D: POST /api/auth/logout/ (Cookie: refresh=...)
    D->>D: Blacklist refresh token
    D->>R: 200 OK + Set-Cookie: access=; Max-Age=0...<br/>Set-Cookie: refresh=; Max-Age=0...
    R->>U: Redirige a /login
```

## Token Lifetimes

| Token | Lifetime | Storage | Rotation |
|-------|----------|---------|----------|
| Access | 15 min | HttpOnly Cookie | No (short-lived) |
| Refresh | 7 days | HttpOnly Cookie | **Yes** (rotated on each use, old blacklisted) |

## Cookie Attributes (Production)

```http
Set-Cookie: access=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...; \
  Path=/; \
  Secure; \
  HttpOnly; \
  SameSite=Lax; \
  Max-Age=900

Set-Cookie: refresh=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...; \
  Path=/; \
  Secure; \
  HttpOnly; \
  SameSite=Lax; \
  Max-Age=604800
```

## Frontend Implementation Details

### 1. App Startup (`main.tsx`)

```tsx
import { initializeCsrf } from '@/api/csrf';
import { api } from '@/api/client';

// Initialize CSRF before any mutations
await initializeCsrf(api);

// Check auth state
try {
  const user = await authApi.me();
  // Set user in context/store
} catch {
  // Not authenticated, stay on login
}
```

### 2. Login Form

```tsx
const handleLogin = async (email: string, password: string) => {
  try {
    const { user } = await authApi.login(email, password);
    // Cookies set automatically by browser
    setUser(user);
    navigate('/dashboard');
  } catch (error) {
    // Handle error (invalid credentials, etc.)
  }
};
```

### 3. Auto-refresh (handled by axios interceptor)

```tsx
// In api/client.ts - automatic on 401
// No manual code needed in components
```

### 4. Logout

```tsx
const handleLogout = async () => {
  await authApi.logout(); // Clears cookies
  setUser(null);
  navigate('/login');
};
```

## Multi-Tenant Gym Context

### Frontend: Set Gym ID

```tsx
// After login, store gym ID
localStorage.setItem('gymId', user.gym_id);

// Or for session-only
sessionStorage.setItem('gymId', user.gym_id);
```

### Axios Interceptor (automatic)

```typescript
// In api/client.ts
const gymId = localStorage.getItem('gymId') || sessionStorage.getItem('gymId');
if (gymId) {
  config.headers['X-Gym-ID'] = gymId;
}
```

### Django Middleware (automatic)

```python
# gimnasioApp/middleware.py
class GymMiddleware:
    GYM_HEADER = 'HTTP_X_GYM_ID'  # X-Gym-ID header
    
    def process_request(self, request):
        gym_id = request.META.get(self.GYM_HEADER)
        if gym_id:
            request.gimnasio = Gimnasio.objects.get(id=gym_id)
```

## Security Checklist

- [ ] `Secure` flag on cookies (HTTPS only)
- [ ] `HttpOnly` flag (no JS access)
- [ ] `SameSite=Lax` (CSRF protection)
- [ ] `CSRF_COOKIE_SAMESITE=Lax` on Django
- [ ] `CORS_ALLOW_CREDENTIALS=True` + specific origins
- [ ] Refresh token rotation + blacklist
- [ ] Short access token lifetime (15 min)
- [ ] Rate limiting on `/auth/login/`
- [ ] CSRF token required for mutations
- [ ] `X-Gym-ID` validated in middleware

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Cookies not sent in dev | `withCredentials: false` | Set `withCredentials: true` in axios |
| CORS error | Missing `CORS_ALLOW_CREDENTIALS` | Add to Django settings |
| 403 on mutations | Missing CSRF header | Call `/auth/csrf/` on startup, send `X-CSRFToken` |
| Refresh loop | Refresh token not rotating | Check `ROTATE_REFRESH_TOKENS=True`, `BLACKLIST_AFTER_ROTATION=True` |
| Gym context lost | Header not forwarded | Verify Vite proxy `configure` passes `X-Gym-ID` |