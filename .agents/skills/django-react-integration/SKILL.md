---
name: django-react-integration
description: "Trigger: Django React integration, CORS, JWT, CSRF, Vite proxy, cookie auth, static build, SPA routing. Django + React/TypeScript integration patterns for ControlFit."
license: Apache-2.0
metadata:
  author: "oscar-personal"
  version: "1.0"
---

# Django + React Integration Patterns for ControlFit

## Activation Contract

Load this skill when configuring or debugging:
- CORS settings for `gimnasioReact` → `gimnasioApp` API
- Authentication: JWT in cookies (HttpOnly) + CSRF
- Vite dev server proxy to Django
- Production static build (`npm run build` → Django `collectstatic`)
- SPA routing fallback (Django serves `index.html` for non-API routes)
- Multi-tenant gym context propagation (header → middleware → request.gimnasio)

## Hard Rules

- **Auth = HttpOnly cookie + CSRF**: JWT in `access`/`refresh` cookies, `Secure; SameSite=Lax`, CSRF token in header `X-CSRFToken`
- **CORS**: only `localhost:5173` (dev) and production domain; no `*`
- **Vite proxy**: `/api` → `http://localhost:8000` in dev only
- **Production**: `npm run build` outputs to `gimnasioApp/static/`, Django serves via WhiteNoise
- **SPA fallback**: Django catch-all view returns `index.html` for non-`/api/`, non-`/admin/`, non-`/static/`, non-`/media/` routes
- **Gym context**: `X-Gym-ID` header from frontend → middleware sets `request.gimnasio` → all queries scoped

## Decision Gates

| Situation | Config |
|-----------|--------|
| Dev (Vite + Django) | Vite proxy `/api` → Django, CORS allow localhost |
| Prod (Django serves React) | `collectstatic` includes `dist/`, WhiteNoise, SPA fallback view |
| Auth login | POST `/api/auth/login/` → sets HttpOnly cookies |
| Auth refresh | POST `/api/auth/refresh/` → rotates refresh, sets new access |
| Auth logout | POST `/api/auth/logout/` → clears cookies |
| CSRF | `getCsrfToken()` call before first mutation, then header |
| Multi-tenant | Frontend sends `X-Gym-ID` header, Django middleware resolves |

## Execution Steps

1. **Configure Django CORS** (`corsheaders`): `CORS_ALLOWED_ORIGINS`, `CORS_ALLOW_CREDENTIALS=True`
2. **Configure Django CSRF**: `CSRF_TRUSTED_ORIGINS`, `CSRF_COOKIE_SAMESITE='Lax'`
3. **Setup JWT cookies** (SimpleJWT): `AUTH_COOKIE` settings, custom `TokenObtainPairView`
4. **Create gym middleware**: extracts `X-Gym-ID` → `Gimnasio` → `request.gimnasio`
5. **Configure Vite proxy** (`vite.config.ts`): `/api` target, `changeOrigin: true`
6. **Build script**: `npm run build && python manage.py collectstatic --noinput`
7. **SPA fallback view**: `TemplateView.as_view(template_name='index.html')` for catch-all
8. **Frontend API client**: axios instance with interceptors (attach CSRF, handle 401 → refresh)

## Output Contract

Return created/modified files:
- Django: `settings/*.py`, `middleware.py`, `auth_cookie.py`, `urls.py` (SPA fallback)
- Vite: `vite.config.ts`, `package.json` scripts
- Frontend: `api/client.ts` (axios + interceptors), `hooks/useAuth.ts`

## References

- `assets/django-cors-settings.py` — CORS + CSRF + cookie config
- `assets/django-jwt-cookie-views.py` — Custom login/refresh/logout views
- `assets/django-gym-middleware.py` — Multi-tenant gym context
- `assets/django-spa-fallback.py` — Catch-all view for SPA routing
- `assets/vite-config.ts` — Vite proxy + build output config
- `assets/frontend-api-client.ts` — Axios + interceptors + auth hooks
- `references/auth-flow.md` — Login/refresh/logout sequence diagram
- `references/deploy-checklist.md` — Prod deployment steps