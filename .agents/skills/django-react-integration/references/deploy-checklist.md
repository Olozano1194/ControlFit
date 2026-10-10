# Deploy Checklist: Django + React (ControlFit)

## Pre-Deploy Verification

### Django Settings (Production)

- [ ] `DEBUG = False`
- [ ] `SECRET_KEY` from env var (not in code)
- [ ] `ALLOWED_HOSTS` = production domain(s)
- [ ] `CORS_ALLOWED_ORIGINS` = production frontend domain only
- [ ] `CSRF_TRUSTED_ORIGINS` = production domain
- [ ] `SECURE_SSL_REDIRECT = True`
- [ ] `SESSION_COOKIE_SECURE = True`
- [ ] `CSRF_COOKIE_SECURE = True`
- [ ] `SIMPLE_JWT.AUTH_COOKIE_SECURE = True`
- [ ] `SIMPLE_JWT.AUTH_COOKIE_DOMAIN = '.tudominio.com'` (subdomain support)
- [ ] Database: PostgreSQL with connection pooling (PgBouncer)
- [ ] Redis: configured for cache + Celery + sessions
- [ ] Email: SMTP configured (password reset, notifications)

### React Build (Production)

- [ ] `npm run build` completes without errors
- [ ] Build output in `gimnasioApp/static/` (or configured `STATICFILES_DIRS`)
- [ ] `manifest.json` generated (for cache busting)
- [ ] Chunk splitting: vendor, query, forms, ui chunks created
- [ ] Sourcemaps generated (upload to Sentry/error tracking)
- [ ] Bundle size acceptable (< 500KB gzipped initial)

### Static Files

- [ ] `python manage.py collectstatic --noinput` succeeds
- [ ] WhiteNoise serves static files (or Nginx/CloudFront)
- [ ] `STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'`
- [ ] Cache headers: `Cache-Control: public, max-age=31536000, immutable` for hashed assets

### Media Files

- [ ] `MEDIA_ROOT` outside codebase (e.g., `/var/www/media/`)
- [ ] Served by Nginx (not Django) in production
- [ ] Signed URLs or private bucket for sensitive uploads

## Deployment Steps

### 1. Build & Collect Static

```bash
# In project root
cd gimnasioReact
npm ci
npm run build

cd ../gimnasioApp
python manage.py collectstatic --noinput
python manage.py migrate --noinput
```

### 2. Run Migrations

```bash
python manage.py migrate --noinput
# Verify no pending migrations
python manage.py showmigrations --plan
```

### 3. Health Checks

```bash
# Django health endpoint
curl -f https://api.tudominio.com/health/

# Frontend loads
curl -f https://tudominio.com/

# API auth works
curl -f -X POST https://api.tudominio.com/api/auth/csrf/
```

### 4. Post-Deploy Verification

- [ ] Login flow works (sets HttpOnly cookies)
- [ ] Refresh token rotation works (wait 15 min, make request)
- [ ] CSRF protection works (mutation without token fails)
- [ ] Multi-tenant gym context works (X-Gym-ID header)
- [ ] SPA routing works (refresh /dashboard, /members/1)
- [ ] Static assets load with correct cache headers
- [ ] Media uploads work
- [ ] Admin panel accessible
- [ ] Error tracking (Sentry) receiving events

## Rollback Plan

```bash
# 1. Revert code
git checkout previous-tag

# 2. Rebuild frontend
cd gimnasioReact && npm run build

# 3. Collect static
cd ../gimnasioApp && python manage.py collectstatic --noinput

# 4. Migrate down if needed (CAREFUL!)
# python manage.py migrate app_name previous_migration

# 5. Restart services
systemctl restart gunicorn
systemctl restart nginx
```

## Monitoring & Alerts

- [ ] Uptime check: `/health/` every 30s
- [ ] Error rate alert: > 1% 5xx in 5 min
- [ ] Response time alert: p95 > 2s
- [ ] Queue depth alert: Celery tasks > 100 pending
- [ ] Disk space alert: > 80% used
- [ ] DB connections alert: > 80% pool used

## Environment Variables (Production)

```bash
# Django
DJANGO_SECRET_KEY=...
DEBUG=False
ALLOWED_HOSTS=api.tudominio.com,tudominio.com
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0
JWT_SECRET_KEY=... (different from DJANGO_SECRET_KEY)
CORS_ALLOWED_ORIGINS=https://tudominio.com
CSRF_TRUSTED_ORIGINS=https://tudominio.com
SIMPLE_JWT_AUTH_COOKIE_DOMAIN=.tudominio.com

# Email
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=...
DEFAULT_FROM_EMAIL=noreply@tudominio.com

# Sentry
SENTRY_DSN=...

# Frontend (build-time)
VITE_API_URL=https://api.tudominio.com
VITE_APP_VERSION=1.2.3
```

## DNS / SSL

- [ ] A/AAAA records for `tudominio.com` and `api.tudominio.com`
- [ ] SSL certificates (Let's Encrypt or managed)
- [ ] HSTS preload submitted
- [ ] CAA records for certificate authority restriction

## Backup Strategy

- [ ] Database: daily automated backups, point-in-time recovery
- [ ] Media files: synced to S3/GCS with versioning
- [ ] Redis: RDB snapshots every 60s
- [ ] Test restore quarterly

## Security Hardening

- [ ] `SECURE_HSTS_SECONDS = 31536000`
- [ ] `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`
- [ ] `SECURE_HSTS_PRELOAD = True`
- [ ] `SECURE_CONTENT_TYPE_NOSNIFF = True`
- [ ] `SECURE_BROWSER_XSS_FILTER = True`
- [ ] `X_FRAME_OPTIONS = 'DENY'`
- [ ] CSP headers configured (report-only first)
- [ ] Rate limiting on auth endpoints
- [ ] Failed login logging + alerting
- [ ] Dependency scanning (pip-audit, npm audit) in CI