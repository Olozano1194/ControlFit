# Design: membership-assignment-business-operations

## Overview

Hybrid separation (Option C): personal data (Miembro) always editable; assignment mutations gated by financial state (`estado_pago`). Free-form assignment edits only when `pending`. For `paid`/`partial`, use explicit operations (suspend/refund/change-plan/renew) with mandatory reason and audit trail. Fix `filterActiveMemberships` to not block personal-only updates. Gate `dateFinal` recomputation to assignment-field changes.

## Architecture

### Domain split
- Member domain: `nuevoName,nuevoLastname,nuevoPhone,nuevoAddress` → Miembro via `updateMember`.
- Assignment domain: `membresia,dateInitial,multiplier,discount_percent` → AsignarMemberShips via `updateAsignarMemberShips` only if dirty AND editable. `dateFinal` derived only on assignment changes.

### State model
- `estado_pago`: `pending | partial | paid`
- `canEditAssignment = (asignacion?.estado_pago === 'pending')`
- Personal: always editable when editing.

## Data Model & API

Existing endpoints reused: `UserGym/{id}/` (PUT), `MemberShipsAsignada/{id}/` (PUT). Future operations (conceptual): `POST /MemberShipsAsignada/{id}/suspender/`, `cambiar-plan/`, `devolucion/` with mandatory `reason`, multi-tenant, audit log recommended.

## UI/UX

Same form split into: (1) Datos personales — always enabled; (2) Membresía asignada — editable only if pending, else read-only + operation actions (Suspender, Cambiar plan, Registrar devolución, Renovar).

## Dirty tracking & submit
- Member dirty if personal fields changed vs initial
- Assignment dirty if assignment fields changed
- If member dirty → `updateMember` always (no assignment validation blocking). If assignment dirty AND editable → `updateAsignarMemberShips` with `dateFinal` recalculated only then. If only member dirty → skip assignment call.

## filterActiveMemberships fix
Edit mode: include current membership (even if inactive/deactivated) in memberships list to avoid blocking member-only saves. Decouple member validation from membership existence for member-only updates.

## Phased Implementation

**Phase 1 (P0)**: domain split, dirty tracking, submit split, recomputation gating, filter fix, UI gating, schema relaxations.  
**Phase 2 (P1)**: suspend + mandatory reason + modal + audit.  
**Phase 3 (P2)**: change-plan with unused-days credit, discount/multiplier via operation.  
**Phase 4 (P2)**: refund/renew.

## Risks & Mitigations
Backend gaps (feature-flag operations), schema conflicts (member-only validation) → domain-aware validation/partial submits, snapshot integrity (operations own snapshots).
