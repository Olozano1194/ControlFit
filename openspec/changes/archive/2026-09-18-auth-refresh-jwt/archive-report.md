# Archive Report: auth-refresh-jwt

## Change Archived

**Change**: auth-refresh-jwt  
**Archived to**: `openspec/changes/archive/2026-09-18-auth-refresh-jwt/`

### Specs Synced

| Domain | Action | Details |
|--------|--------|---------|
| user-auth | Updated | 25 requirements added from auth-refresh-jwt delta spec; existing password change requirements preserved |

### Archive Contents

- proposal.md ✅
- specs/ ✅ (auth/spec.md — 291 lines covering cookie-setting login, refresh with rotation, multi-tab rotation, server-side logout, frontend contract preservation, on-mount session restore, server-side logout call, axiosPublic fix, config cleanup, auth integration tests)
- design.md ✅
- tasks.md ✅ (5/5 phases complete; Phase 6 manual browser tests are expected unchecked items)

### Source of Truth Updated

The following specs now reflect the new behavior:
- `openspec/specs/user-auth/spec.md` — merged auth-refresh-jwt requirements for cookie-setting login, refresh with rotation, multi-tab rotation behavior, server-side logout, frontend contract preservation, on-mount session restore, server-side logout call, duplicate axiosPublic fix, config cleanup, and auth integration tests

### SDD Cycle Complete

The change has been fully planned, implemented, verified, and archived.

- **Implemented**: Backend (auth_cookie.py, views/auth_views.py, urls.py, settings.py) and Frontend (users.api.ts, AuthProvider.tsx, authStorage.ts) updates completed
- **Verified**: All 138 tests pass (both Django and pytest); Phase 6 manual browser tests are the only unchecked items (expected)
- **Synced**: Delta specs merged into main user-auth specification
- **Archived**: Change folder moved to `openspec/changes/archive/2026-09-18-auth-refresh-jwt/`

Ready for the next change.