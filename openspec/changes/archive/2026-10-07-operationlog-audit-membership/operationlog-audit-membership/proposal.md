# Proposal: OperationLog Audit for Membership Business Operations

## Intent

The 4 membership operations (suspender, cambiar-plan, devolucion, renovar) validate a mandatory reason but record NO audit trail — archived TODOs mark the gap. Add a dedicated `OperationLog` model so every operation is traceable: who, when, why, what changed. Makes Requirement 4 (audit metadata) of `membership-assignments` real.

## Scope

### In Scope
- New `OperationLog` model (gimnasio FK, membresia_asignada FK, operation_type enum, usuario FK nullable, reason, details JSONField, created_at)
- Migration `0015_operationlog`
- `log_operation()` helper (single creation point, no 4x duplication)
- Integration in all 4 `@action` endpoints, TODOs removed
- Superadmin-safe gimnasio (from assignment); `renovar` logs ORIGINAL assignment
- Tests: log creation per operation + tenant isolation

### Out of Scope
- Admin UI for logs (separate feature)
- API exposure / OperationLog serializer (later)
- Backfill of historical operations

## Capabilities

### New Capabilities
- `operation-log`: OperationLog model, multi-tenant isolation, audit fields, and per-operation `details` snapshots

### Modified Capabilities
- `membership-assignments`: Requirement 4 (audit metadata) now backed by OperationLog; all 4 operations MUST persist an entry on success

## Approach

Follow existing model conventions (`Meta.db_table`, `ordering`, `__str__`, `gimnasio` FK, `auto_now_add`). One helper `log_operation(request, asignacion, operation_type, reason, details)` in `gimnasioApp/views/membership_audit.py`, called by all 4 actions. gimnasio from `asignacion.miembro.gimnasio` (superadmin-safe), usuario = `request.user`. `renovar` logs against the ORIGINAL assignment; new id goes in `details`. Snapshots: suspender `{dias, original_date_final, new_date_final}`; cambiar_plan `{membresia_anterior, membresia_nueva, credit, final_price}`; devolucion `{monto, total_pagado_before}`; renovar `{nueva_asignacion_id, membresia, price}`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `gimnasioApp/models/operation_log_model.py` | New | OperationLog model |
| `gimnasioApp/models/__init__.py` | Modified | Export OperationLog |
| `gimnasioApp/views/membership_views.py` | Modified | 4 actions call log_operation, TODOs removed |
| `gimnasioApp/views/membership_audit.py` | New | log_operation helper |
| `gimnasioApp/migrations/0015_operationlog.py` | New | Create table |
| `gimnasioApp/tests/...` | New | Log-creation tests + isolation test |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| renovar logs against wrong assignment | Med | Helper takes explicit assignment arg; test asserts original FK |
| Superadmin log misses gimnasio | Med | Resolve gimnasio from assignment; dedicated test |
| details schema drift between operations | Low | Test asserts required keys per operation_type |
| Migration conflicts | Low | Depends on latest migration only |

## Rollback Plan

Reverse migration `0015` and revert the 4 view edits (restore TODO markers). No data migration — safe.

## Dependencies

- None (self-contained). Follows archived `membership-assignment-business-operations` contracts.

## Success Criteria

- [ ] All 4 operations create an OperationLog on success (correct type, reason, gimnasio)
- [ ] Superadmin operations logged with gimnasio from assignment
- [ ] renovar log references ORIGINAL assignment; new id in details
- [ ] Tenant isolation: logs scoped to same gimnasio
- [ ] Existing 39 backend tests pass; new tests cover log creation per operation

## Recommended First Slice

Model + migration + helper + suspender integration + its test. Land that, then repeat the trivial helper call for the other 3 operations in one follow-up slice.
