# Phase 1 Core Hardening — Delta Specifications

## Testing Infrastructure

| Requirement | Description |
|-------------|-------------|
| SQLite Test Database | Configure `DATABASES['default']['TEST'] = {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}` for tests only |
| CI Pipeline Without MySQL | GitHub Actions workflow runs tests without MySQL service on ubuntu-latest |
| Test Performance | Test suite completes in <10 seconds locally |
| Migration Compatibility | SQLite test database supports all Django migrations |

## Platform Analytics

| Requirement | Description |
|-------------|-------------|
| Numeric Response Types | Return `retencion_promedio` as number (not string) with one decimal place |
| DecimalField Configuration | Configure `PlatformStatsSerializer.retencion_promedio` with `coerce_to_string=False` |
| Frontend Type Handling | Update `PlatformDashboardPage.tsx` to handle number, remove `.toFixed()` |
| Regression Prevention | Tests validate `retencion_promedio` is number, not string |

## Data Cleanup

| Requirement | Description |
|-------------|-------------|
| Remove notified_at Field | Remove deprecated `notified_at` from `MembresiaAsignada` model |
| No Code References | No code references to `notified_at` after removal |
| Migration Safety | Generate `RemoveField` migration, reversible for rollback |
| Notification Model Unaffected | `Notification` model continues working after change |

## Tenant Safety

| Requirement | Description |
|-------------|-------------|
| ActiveManager Implementation | `ActiveManager` filters `is_active=True` by default |
| Gimnasio Active Filtering | `Gimnasio.objects` returns only active; `all_objects` returns all |
| Usuario Active Filtering | `Usuario.objects` returns only active; `all_objects` returns all |
| Code Audit | Audit `.objects` usages in views/services; admin uses `all_objects` |
| Migration Safety | Manager change is Python-level, no migrations required |

## Gym Country Code

| Requirement | Description |
|-------------|-------------|
| Country Code Field | Add `country_code = CharField(max_length=5, default='57')` to `Gimnasio` |
| Migration with Default | Generate migration adding field with default '57' |
| Configurable WhatsApp Links | Update `_construir_whatsapp_link()` to use `gimnasio.country_code` |
| Backward Compatibility | Default '57' preserves current behavior |

## Security Audit

| Requirement | Description |
|-------------|-------------|
| Public Access Documentation | Document `RegisterViewSet` intentional public access (AllowAny) |
| Threat Model Documentation | Document threats: spam, abuse, unauthorized access |
| Rate Limiting Consideration | Document rate limiting SHOULD be implemented |
| Spam Protection Consideration | Document spam protection measures |
| No Code Changes | Audit-only task, no behavior changes |

## User Auth

| Requirement | Description |
|-------------|-------------|
| E2E Forced Password Change Test | Test complete flow: login → 403 → password change → 200 access |
| JWT Cookie Flow | Test JWT cookie-based authentication with Django test client |
| Password Change Endpoint | Test `POST /auth/password/change/` with old_password, new_password, confirm_password |
| Access Restoration | After password change, user can access protected endpoints |

## Demo Request Soft Delete

| Requirement | Description |
|-------------|-------------|
| Soft Delete Implementation | `destroy()` sets `estado='cancelada'` instead of hard delete |
| Estado Transition Validation | Only `pendiente` or `contactado` can be cancelled; already cancelled cannot |
| Serializer Validation | Update `DemoRequestSerializer` to validate estado transitions |
| Frontend Delete Button | Add delete button with confirmation modal to `DemoRequestsPage.tsx` |
| API Response Format | Return updated object with `estado='cancelada'` after soft delete |
| Frontend API Integration | Update `demoRequests.api.ts` with DELETE call |