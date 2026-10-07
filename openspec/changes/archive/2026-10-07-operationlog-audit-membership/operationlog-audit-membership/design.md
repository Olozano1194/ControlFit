# Design: OperationLog Audit for Membership Operations

## Technical Approach

Add append-only `OperationLog` (spec REQ-1..6) + helper `log_operation()` (BR-1) at the 4 TODO sites in `membership_views.py`. Gimnasio from the assignment (REQ-2); `renovar` logs the original row (REQ-3). Each action wraps mutation + log in `transaction.atomic()` so no operation persists unaudited. No serializer/API/UI/backfill (NFR-4).

## Architecture Decisions

| Decision | Alternatives | Rationale |
|---|---|---|
| Model in `models/operation_log_model.py` | inside `membership_model.py` | one-model-per-file convention (`payment_model`) |
| Helper in `views/membership_audit.py` | inline per action; `services/` | BR-1 single entry point; views already split by concern |
| `gimnasio` FK: CASCADE | PROTECT | matches all tenant FKs; member deletion must keep working |
| `membresia_asignada` FK: CASCADE | SET_NULL (breaks non-null spec); PROTECT (blocks deletes) | spec requires non-null; append-only (REQ-6) governs app code, not cascade |
| `usuario` FK: SET_NULL, null | CASCADE | mirrors `EventoCalendario.created_by`; user deletion preserves rows |
| gimnasio from `asignacion.miembro.gimnasio` | `request.gimnasio` | REQ-2: superadmin has no request tenant |
| `transaction.atomic()` around mutation+log | plain call; try/except swallow | swallow = silent audit loss; plain call risks unlogged persisted op; precedent in `member_serializer.py` |
| `details`: Decimal→`str`, date→`.isoformat()` | DjangoJSONEncoder | default encoder rejects Decimal; strings avoid float drift |
| `Meta.indexes`: `(gimnasio, created_at)`, `(membresia_asignada, created_at)` | none (no precedent) | only read paths: tenant listing + per-assignment history |

## Data Flow

    POST /gym/api/v1/membresias-asignadas/{id}/suspender
        → validate_* (failure → 400, no log — REQ-1)
        → atomic { apply_* mutation → log_operation() }   # gimnasio ← asignacion.miembro.gimnasio
        → serializer(response unchanged — NFR-1)

## File Changes

| File | Action | Description |
|---|---|---|
| `gimnasioApp/models/operation_log_model.py` | Create | model (below) |
| `gimnasioApp/models/__init__.py` | Modify | export `OperationLog` |
| `gimnasioApp/views/membership_audit.py` | Create | `log_operation()` |
| `gimnasioApp/views/membership_views.py` | Modify | 4 actions: atomic + call; drop TODOs |
| `gimnasioApp/migrations/0015_operationlog.py` | Create | table + indexes |
| `gimnasioApp/tests/test_operation_log.py` | Create | REQ tests |

## Interfaces / Contracts

### Model (`operation_log_model.py`)

```python
class OperationLog(models.Model):
    class OperationType(models.TextChoices):
        SUSPENDER = 'suspender'; CAMBIAR_PLAN = 'cambiar_plan'
        DEVOLUCION = 'devolucion'; RENOVAR = 'renovar'
    gimnasio = FK(Gimnasio, CASCADE, related_name='operation_logs')
    membresia_asignada = FK(MembresiaAsignada, CASCADE, related_name='operation_logs')
    operation_type = CharField(max_length=20, choices=OperationType.choices)
    usuario = FK(settings.AUTH_USER_MODEL, SET_NULL, null=True, blank=True,
                 related_name='operation_logs')
    reason = TextField()                    # verbatim, BR-2
    details = JSONField(default=dict)       # schema per REQ-4
    created_at = DateTimeField(auto_now_add=True)
    # Meta: db_table='operation_log', ordering=['-created_at'], indexes as per D9
    def __str__(self): return f'{self.operation_type} #{self.pk} {self.created_at:%Y-%m-%d}'
```

### Migration `0015_operationlog.py`

Depends on `('gimnasioApp', '0014_gimnasio_country_code')`. Operations: `CreateModel` (fields above, `id` = `BigAutoField`) + `AddIndex` ×2, generated via `makemigrations`. Forward CREATE TABLE / reverse DROP TABLE; no data migration.

### Helper (`views/membership_audit.py`)

```python
def log_operation(request, asignacion, operation_type, reason, details=None):
    """Single audit entry point (BR-1)."""
    user = getattr(request, 'user', None)
    return OperationLog.objects.create(
        gimnasio=asignacion.miembro.gimnasio,           # REQ-2: never request tenant
        membresia_asignada=asignacion,                 # REQ-3: caller passes original
        operation_type=operation_type,
        usuario=user if getattr(user, 'is_authenticated', False) else None,
        reason=reason,                                  # BR-2: verbatim
        details=details or {},
    )
```

### Integration — the 4 actions (`membership_views.py`)

| Action | Placement / captured values | `details` (REQ-4) |
|---|---|---|
| `suspender` | after `apply_suspension`; capture its return (`original_date_final`) | `{dias, original_date_final: iso, new_date_final: asignacion.dateFinal.isoformat()}` |
| `cambiar_plan` | after `apply_cambiar_plan` + `refresh_from_db` | `{membresia_anterior: original_membresia.id, membresia_nueva: nueva_membresia.id, credit: str(credit), final_price: str(final_price)}` |
| `devolucion` | capture `asignacion.total_pagado` BEFORE `create_refund_payment`, log after | `{monto: str(monto), total_pagado_before: str(before)}` |
| `renovar` | after `create_renewal_assignment`; pass ORIGINAL `asignacion` (not `nueva_asignacion`) | `{nueva_asignacion_id, membresia: membresia.id, price: str(price)}` |

`with transaction.atomic():` wraps mutation + log; `reason = request.data.get('reason')`; response untouched (NFR-1).

## Testing Strategy

Strict TDD. Pattern: `TestCase` + `APIRequestFactory` + `force_authenticate` + `factories.py`; 165 existing tests stay green.

| REQ | Test | Key assertions |
|---|---|---|
| REQ-1 | `test_suspender_creates_log` | count +1; type=`suspender`; reason verbatim; `usuario` = acting user; `created_at` set |
| REQ-1 | `test_rejected_operation_no_log` | 400 → count unchanged, assignment unchanged |
| REQ-2 | `test_superadmin_log_uses_assignment_gimnasio` | superadmin, `request.gimnasio=None` → row.gimnasio == assignment gym |
| REQ-3 | `test_renovar_logs_original_assignment` | `membresia_asignada_id` == original pk; `details['nueva_asignacion_id']` == new pk |
| REQ-4 | `test_details_keys_per_operation_type` | run all 4; each row holds its required key set |
| REQ-5 | `test_tenant_isolation` | rows in G1/G2; `filter(gimnasio=G1)` excludes G2 |
| BR-1 | `test_log_operation_ignores_request_gimnasio` | direct helper call with spoofed `request.gimnasio` |

Unit: helper; integration: 4 endpoints; E2E: none.

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Migration / Rollout

Single migration, write-only feature, no flag, no backfill. **Rollback**: (1) `manage.py migrate gimnasioApp 0014` drops table (auto-reverse, NFR-3); (2) revert view edits (TODOs restored); (3) verify: `manage.py check` clean, endpoints return 200 unchanged, `python manage.py test gimnasioApp` green.

## Future (out of scope — NFR-4)

`OperationLogSerializer` (read-only) + `GET`-only router resource with `MultiTenantViewSetMixin`; TS mirror already drafted in spec. Never expose writes (append-only).

## Open Questions

None. Proposal and specs close all decisions.
