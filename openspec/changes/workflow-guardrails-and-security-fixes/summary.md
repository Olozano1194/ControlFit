# Workflow Guardrails, CI Repair & Dependency Security Fix

## Summary

Added contribution workflow guardrails, repaired failing GitHub Actions CI, and fixed real
dependency vulnerabilities across backend (pip) and frontend (npm). All changes pushed to
branch `OscarL`; PR to `master` should now pass both CI jobs.

## Commits (pushed to origin/OscarL)

| Hash | Message |
|------|---------|
| f323b49 | chore(flujo): agregar reglas de contribución y guardrails |
| 9a5bfec | chore(hooks): marcar hooks como ejecutables |
| ef14545 | fix(deps): actualizar dependencias con vulnerabilidades |
| cc96c45 | fix(ci): usar SQLite en el check de GitHub Actions |
| ea86246 | fix(lint): corregir any e import sin usar |
| f9f0c8f | fix(hooks): validar el gate contra el venv del proyecto |

## Changes

### Workflow guardrails (`AGENTS.md`)
- Approval gate before `git commit`/`git push` (human explicit approval required).
- Verification gate (frontend: tsc + lint + test; backend: check + tests).
- Junior-readable code rules, branch/PR conventions, testing, docs, 250-line reminder.
- Hooks section documenting `.githooks/`.

### Hooks (`.githooks/`)
- `pre-commit`: blocks new code files >250 lines; runs frontend typecheck + lint on changes.
- `pre-push`: uses project venv python (`env/Scripts/python.exe`), runs `pip check`, backend tests, frontend gate.
- `commit-msg`: conventional commits with Spanish descriptions, no AI attribution.
- All three marked executable (`100755`).

### PR template (`.github/PULL_REQUEST_TEMPLATE.md`)
- Checklist for change description, testing, risks, rollback.

### CI (`.github/workflows/ci.yml`)
- Backend job: `pip install -r requirements.txt`, `manage.py check`, `manage.py test gimnasioApp` with `DATABASE_URL: "sqlite:///:memory:"`.
- Frontend job: `npm ci`, `tsc -b`, `npm run lint`, `npm test`.

### Dependency security
- Backend (`requirements.txt`): upgraded Django, DRF, Pillow, PyJWT, requests, sqlparse, Brotli, setuptools, django-storages; removed unused `pymongo` and `dnspython`; moved `mysqlclient` to `requirements-dev.txt`.
- Frontend (`package-lock.json`): axios, vite, vitest, zod and transitive deps.
- `gimnasio/settings.py`: DRF schema class `coreapi.AutoSchema` -> `openapi.AutoSchema` (DRF 3.18 removed coreapi).
- `pip-audit`: 0 vulnerabilities. `npm audit`: 0 vulnerabilities.

### Lint fixes
- `AuthProvider.tsx`: `catch (error: any)` -> `unknown` with typed cast.
- `DemoRequestsPage.toggle.error.test.tsx`: removed unused `act` import.

## Verification

- `pip-audit`: 0 vulnerabilities.
- `npm audit`: 0 vulnerabilities.
- Backend: `manage.py check` OK, 181 tests OK.
- Frontend: `tsc` OK, `lint` OK, 252 tests OK.
- `pre-push` gate: passed.

## Key learnings

- GitHub reports 188 vulnerabilities by summing npm + pip + dev + transitive + duplicates; real counts were 13 npm + 84 pip advisories.
- `mysqlclient` only ships Windows wheels; on Ubuntu it compiles and fails without `libmysqlclient-dev`. Production uses Postgres, so it moved to dev requirements.
- `manage.py check` fails with `DATABASE_URL=""` (empty DB config); CI uses `sqlite:///:memory:`.
- Committed lint errors were fixed by the user's in-progress WIP; verified in a clean worktree.
- `npm audit fix` updates the lockfile but not `node_modules`; `npm ci` was required to sync.
- DRF 3.18 removed `rest_framework.schemas.coreapi.AutoSchema`.
- Free Beam model can drop transiently (rate limit/provider); Gentle-Orchestrator uses `opencode/beam-free`.

## Status

- Branch `OscarL` pushed and in sync with `origin/OscarL`.
- User WIP (memberForm refactor, DemoRequestList, etc.) left uncommitted.
- PR to `master` expected to pass both CI jobs.