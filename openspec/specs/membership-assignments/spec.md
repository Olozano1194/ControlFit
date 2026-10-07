# Spec: Member Assignment Business Operations

## Delta
This change separates member personal data editing from assignment/accounting mutations for membership assignments (`AsignarMemberShips`).

## Requirements

### Requirement 1: Personal data is always editable

**User Story:** As an admin, I can edit a member's personal data (name, lastname, phone, address) at any time regardless of assignment state.

**Acceptance Criteria**

1. MUST allow editing `name`, `lastname`, `phone`, `address` on the member (Miembro/UserGym) even when the assignment is `paid`, `partial`, or `expired`.
2. MUST persist personal data changes via `updateMember` (separately from assignment updates).
3. MUST NOT block saving personal data due to `filterActiveMemberships` excluding the original plan (if deactivated after sale).
4. MUST keep personal data fields enabled in the edit form for all assignment states.
5. SHOULD allow saving personal data changes independently without requiring assignment field changes.

### Requirement 2: Separate domain updates

**User Story:** As a system, updates to personal data and assignment/accounting must not be coupled in a way that causes accidental mutation.

**Acceptance Criteria**

1. MUST compute `dateFinal` only when assignment fields (`membresia`, `dateInitial`, `multiplier`) actually change (not on pure personal-data edits).
2. MUST NOT silently recalculate `dateFinal` when only member fields change.
3. MUST only call `updateAsignarMemberShips` when assignment fields are modified; call `updateMember` when member fields are modified (or both if both changed).
4. SHOULD avoid requiring a valid/active membership in the select list solely to save member personal data.

### Requirement 3: Assignment editability by financial state

**User Story:** As an admin, assignment fields (membership, start date, multiplier, discount) must only be freely editable when safe, and otherwise changed via explicit operations.

**Acceptance Criteria**

1. MUST treat assignment as not freely editable when `estado_pago` is `paid` or `partial` (financially settled/active with payments). Free-form assignment edits for these states are NOT allowed.
2. MUST allow minimal safe free-form edits of assignment fields only when `estado_pago === 'pending'` (no payments recorded / unpaid). Even then, dateFinal recomputation MUST only occur if assignment fields changed.
3. MUST block free-form assignment edits for expired assignments when financial state is `paid`/`partial`.
4. SHOULD use explicit business operations (suspend, refund, change-plan, renew) for changes to assignments with `paid`/`partial` state.
5. MUST preserve accounting snapshot fields (`price`, `total_pagado`, `saldo_pendiente`, `estado_pago`) — free-form edits MUST NOT overwrite snapshots except via defined operations.

### Requirement 4: Business operations (append-only) with audit

**User Story:** As an admin, I can perform business operations on assignments to handle exceptions with full audit trail.

**Acceptance Criteria**

1. MUST require a mandatory `reason` for operations: `suspend`, `refund`, and `change-plan`. Renewals SHOULD also capture a reason when applicable.
2. MUST record audit metadata for operations: actor (user), timestamp, operation type, reason, affected fields (before/after), assignment ID (multi-tenant scoped).
3. MUST treat assignment mutations for `paid`/`partial` states as operations (append-only) rather than PUT overwrites.
4. SHOULD support `suspend` for `paid` and `partial` states. Suspension operations determine new end date without silently recomputing on generic save.
5. SHOULD support `change-plan` mid-period with unused-days credit calculation conceptually; if implemented, discount/multiplier adjustments MUST be part of the operation (not free-form).
6. SHOULD support `refund` as explicit operation recording amount and reason.
7. MAY implement operations incrementally: Phase 1 (domain separation + filter + recomputation gating), Phase 2 (suspend + mandatory reason), Phase 3 (change-plan with credit + discount/multiplier via operation).

**(Previously: AC 2 required audit metadata generically with no persistence contract; it is now backed by the OperationLog model.)**
### Requirement 5: Filter semantics and validation

**User Story:** As a system, membership list filtering must not interfere with personal data updates.

**Acceptance Criteria**

1. MUST ensure `filterActiveMemberships` does not block saving member personal data when the originally assigned membership is inactive, unavailable, or filtered out.
2. MUST decouple member-field validation from assignment membership existence when only member fields are being updated.
3. MUST apply multi-tenant scoping (`gimnasio`) to all operations and queries (per project rules: MultiTenantViewSetMixin + gimnasio FK).

### Requirement 6: UI behavior (same form, clear separation)

**User Story:** As an admin, the edit form remains compact (same page) with clear domain separation.

**Acceptance Criteria**

1. MUST keep personal data section always enabled in edit mode for all states.
2. MUST gate assignment/pricing fields (membership, dateInitial, multiplier, discount) based on editability (Req 3). For states requiring operations (`paid`/`partial`), present operation actions/modals instead of free-form inputs.
3. SHOULD avoid cross-field validation that prevents saving member-only changes.
4. MUST only submit assignment changes when assignment fields are dirty; only submit member changes when member fields are dirty.
