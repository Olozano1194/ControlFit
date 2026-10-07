# Delta for membership-assignments

## MODIFIED Requirements

### Requirement 4: Business operations (append-only) with audit

**User Story:** As an admin, I can perform business operations on assignments to handle exceptions with full audit trail.

**Acceptance Criteria**

1. MUST require a mandatory `reason` for operations: `suspend`, `refund`, and `change-plan`. Renewals SHOULD also capture a reason when applicable.
2. MUST record audit metadata for every successful operation as an `OperationLog` entry: actor (`usuario`, nullable), timestamp (`created_at`), operation type, reason, `details` snapshot of affected fields (before/after), and the affected assignment ID — all scoped to the assignment's `gimnasio` (never from request tenant context).
3. MUST treat assignment mutations for `paid`/`partial` states as operations (append-only) rather than PUT overwrites.
4. SHOULD support `suspend` for `paid` and `partial` states. Suspension operations determine new end date without silently recomputing on generic save.
5. SHOULD support `change-plan` mid-period with unused-days credit calculation conceptually; if implemented, discount/multiplier adjustments MUST be part of the operation (not free-form).
6. SHOULD support `refund` as explicit operation recording amount and reason.
7. MAY implement operations incrementally: Phase 1 (domain separation + filter + recomputation gating), Phase 2 (suspend + mandatory reason), Phase 3 (change-plan with credit + discount/multiplier via operation).

(Previously: AC 2 required audit metadata generically with no persistence contract; it is now backed by the `OperationLog` model.)

#### Scenario: successful operation is audited

- GIVEN a `paid` assignment in gimnasio G
- WHEN an admin performs `suspend` with a reason
- THEN an `OperationLog` row exists with type `suspender`, the actor, the reason, and `gimnasio = G`

#### Scenario: rejected operation is not audited

- GIVEN the same assignment
- WHEN operation validation fails
- THEN no `OperationLog` row exists and the assignment is unchanged
