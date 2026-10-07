# Tasks: OperationLog Audit for Membership Operations

## Review Workload Forecast

Estimated changed lines: ~380–430 (tests ~230, rest ~150). Delivery strategy: ask-on-risk.

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | PR | Focused test command | Runtime harness | Rollback boundary |
|---|---|---|---|---|---|
| 1 | T01–T06: model, migration, helper, suspender | PR 1 | `manage.py test gimnasioApp.tests.test_operation_log` | `manage.py test gimnasioApp` (django runner) | 4 new files + suspender edit |
| 2 | T07–T13: actions, tests, verify | PR 2 | `manage.py test gimnasioApp.tests.test_operation_log` | `manage.py test gimnasioApp` | `membership_views.py` edits |

## P0: Foundation (RED)

- [ ] **T01** Create `gimnasioApp/tests/test_operation_log.py` with RED `test_suspender_creates_log` — REQ-1: count +1, type, verbatim reason, `usuario`, `created_at`. Dep: — · 30m · AC: RED.
- [ ] **T02** Add RED `test_rejected_operation_no_log` — REQ-1: 400 → no row, assignment unchanged; and `test_log_operation_ignores_request_gimnasio` — BR-1: helper call, spoofed `request.gimnasio`. Dep: T01 · 20m · AC: both RED.

## P1: Model + Migration + Helper (GREEN)

- [ ] **T03** Create `gimnasioApp/models/operation_log_model.py` per design (TextChoices ×4; FKs CASCADE/CASCADE/SET_NULL; Meta db_table + ordering + 2 indexes; `__str__`) + export in `models/__init__.py`. Dep: T02 · 30m · AC: `makemigrations --dry-run` lists only `0015_operationlog`.
- [ ] **T04** Generate `gimnasioApp/migrations/0015_operationlog.py` — depends `0014_gimnasio_country_code`; CreateModel (BigAutoField id) + AddIndex ×2. Dep: T03 · 20m · AC: migrate forward+reverse OK; `manage.py check` clean.
- [ ] **T05** Create `gimnasioApp/views/membership_audit.py::log_operation()` — gimnasio ← `asignacion.miembro.gimnasio`, usuario authenticated-or-None, `details or {}`. Dep: T04 · 25m · AC: T01+T02 green.

## P2: View Integration (RED → GREEN per action)

- [ ] **T06** `suspender`: wrap mutation+log in `transaction.atomic()`, capture `original_date_final`, details `{dias, original_date_final, new_date_final}` (iso), drop 2 TODOs. Dep: T05 · 30m · AC: T01 green; response unchanged.
- [ ] **T07** RED `test_cambiar_plan_creates_log`, then `cambiar_plan`: atomic; log after `refresh_from_db`; details `{membresia_anterior, membresia_nueva, credit, final_price}` (Decimals → str); drop TODOs. Dep: T06 · 30m · AC: RED then green.
- [ ] **T08** RED `test_devolucion_creates_log`, then `devolucion`: capture `total_pagado` before `create_refund_payment`; atomic; details `{monto, total_pagado_before}`; drop TODOs. Dep: T07 · 30m · AC: RED then green.
- [ ] **T09** RED `test_renovar_logs_original_assignment`, then `renovar`: atomic; log ORIGINAL `asignacion` after `create_renewal_assignment`; details `{nueva_asignacion_id, membresia, price}`; drop TODOs. Dep: T08 · 30m · AC: FK = original, details id = new (REQ-3); RED then green.

## P3: Tests (spec coverage)

- [ ] **T10** Add `test_superadmin_log_uses_assignment_gimnasio` — REQ-2: `request.gimnasio=None` → row gym = assignment gym; and `test_tenant_isolation` — REQ-5: G1 query excludes G2. Dep: T09 · 30m · AC: both green.
- [ ] **T11** Add `test_details_keys_per_operation_type` — REQ-4: all 4 ops, required key sets; and `test_history_append_only` — REQ-6. Dep: T10 · 30m · AC: green; 8 tests total (7 REQ + BR-1).
- [ ] **T12** Refactor: only `log_operation()` creates rows, zero `Audit log: TODO` markers, conventions kept. Dep: T11 · 15m · AC: grep clean.

## P4: Verify

- [ ] **T13** `manage.py check` + full `manage.py test gimnasioApp`; rollback drill `migrate gimnasioApp 0014` → re-migrate. Dep: T12 · 20m · AC: check clean, suite green (existing + 8 new), rollback OK, endpoints unchanged.
