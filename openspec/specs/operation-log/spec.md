# OperationLog Specification

## Purpose

Append-only audit trail for the 4 membership business operations (`suspender`, `cambiar_plan`, `devolucion`, `renovar`): who, when, why, what changed — scoped to the owning gym.

## Requirements

### REQ-1: One audit entry per successful operation (SC 1)

The system MUST persist exactly one `OperationLog` row per successful operation with `usuario`, `created_at`, `operation_type`, `reason`, and `details`. Rejected operations MUST NOT create a row.

#### Scenario: suspender success creates a log

- GIVEN a `paid` assignment in gimnasio G and a valid reason
- WHEN an admin performs `suspender`
- THEN one row exists with `operation_type=suspender`, that reason, and `usuario` = acting user

#### Scenario: rejected operation creates no log

- GIVEN an operation request failing validation
- WHEN the request is rejected
- THEN no row exists and the assignment is unchanged

### REQ-2: Superadmin-safe gimnasio resolution (SC 2)

The system MUST set `gimnasio` from the assignment (`asignacion.miembro.gimnasio`) and MUST NOT derive it from request tenant context.

#### Scenario: superadmin operation records owning gym

- GIVEN a superadmin acting on an assignment of gimnasio G with no request tenant
- WHEN the operation succeeds
- THEN the row has `gimnasio = G`

### REQ-3: Renewal logs the original assignment (SC 3)

For `renovar`, `membresia_asignada` MUST be the ORIGINAL assignment; the new id MUST be stored in `details.nueva_asignacion_id`.

#### Scenario: renewal references original

- GIVEN assignment A1
- WHEN `renovar` succeeds creating A2
- THEN the row references A1 and `details.nueva_asignacion_id = A2.id`

### REQ-4: operation_type enum and details snapshots

`operation_type` MUST be one of the 4 values; `details` MUST contain the required keys for its type:

| operation_type | Required `details` keys |
| --- | --- |
| `suspender` | `dias`, `original_date_final`, `new_date_final` |
| `cambiar_plan` | `membresia_anterior`, `membresia_nueva`, `credit`, `final_price` |
| `devolucion` | `monto`, `total_pagado_before` |
| `renovar` | `nueva_asignacion_id`, `membresia`, `price` |

#### Scenario: snapshot keys per operation

- GIVEN each of the 4 operations executed successfully
- WHEN every row is inspected
- THEN `details` contains all keys required for its `operation_type`

### REQ-5: Tenant isolation (SC 4)

Rows MUST carry the assignment's `gimnasio`; queries MUST filter by `gimnasio`, so one gym's logs are never exposed to another.

#### Scenario: cross-gym invisibility

- GIVEN rows exist for gimnasio G1 and G2
- WHEN a G1-scoped query reads logs
- THEN only G1 rows are returned and G2 rows are excluded

### REQ-6: Append-only history

Application code MUST NOT update or delete `OperationLog` rows; rows are immutable once written.

#### Scenario: history preserved

- GIVEN a logged suspension
- WHEN later operations run on the same assignment
- THEN earlier rows are unchanged and new rows are appended

## Business Rules

- BR-1: All audit writes go through a single entry point `log_operation(request, asignacion, operation_type, reason, details)` in `gimnasioApp/views/membership_audit.py` — no per-endpoint duplication.
- BR-2: `reason` is mandatory for all 4 operations (existing endpoint validation) and stored verbatim.
- BR-3: `gimnasio` always resolved from the assignment; `usuario` from `request.user` (nullable for system actors).
- BR-4: `renovar` audits the ORIGINAL assignment; the successor id exists only in `details`.

## Data Contracts

### Django model — `OperationLog` (`gimnasioApp/models/operation_log_model.py`)

| Field | Type | Constraints |
| --- | --- | --- |
| `id` | AutoField | PK |
| `gimnasio` | FK Gimnasio | non-null; tenant scope |
| `membresia_asignada` | FK MembresiaAsignada | non-null; original row for `renovar` |
| `operation_type` | CharField(20) | enum of the 4 operation types |
| `usuario` | FK User | nullable |
| `reason` | TextField | non-empty |
| `details` | JSONField | default `{}`; schema per REQ-4 |
| `created_at` | DateTimeField | `auto_now_add` |

Conventions: `Meta.db_table`, `Meta.ordering = ['-created_at']`, `__str__`.

### TypeScript mirror (frontend; API exposure is out of scope for this change)

```ts
type OperationType = 'suspender' | 'cambiar_plan' | 'devolucion' | 'renovar';

interface OperationLog {
  id: number;
  gimnasio: number;
  membresiaAsignada: number;
  operationType: OperationType;
  usuario: number | null;
  reason: string;
  details: Record<string, unknown>;
  createdAt: string; // ISO 8601
}
```

## Non-Functional Requirements

- NFR-1: Audit writes MUST NOT change operation endpoints' response payloads or status codes.
- NFR-2: All 39 existing backend tests MUST pass; new tests MUST cover log creation per operation type, superadmin gimnasio, `renovar` original-FK, per-type `details` keys, and tenant isolation.
- NFR-3: Migration `0015_operationlog` MUST be reversible; rollback requires no data migration.
- NFR-4: No admin UI, serializer, API endpoint, or historical backfill in this change.
