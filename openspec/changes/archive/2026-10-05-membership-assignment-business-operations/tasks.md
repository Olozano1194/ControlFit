# Tasks: membership-assignment-business-operations

## Phase 1: Fix blockers (P0)

### T001 [P0] Update useMemberFormData to include current membership in edit mode
- File: `src/hooks/useMemberFormData.ts`
- Action: When editing (`id` present), include current membership (asignacion.membresia/membresia_details) even if filtered out by `filterActiveMemberships` (union by id).
- Acceptance: Edit loads when original plan inactive; member-only updates not blocked.
- Depends on: None
- [x] COMPLETE - Implemented in useMemberFormData.ts using mergeCurrentMembership

### T002 [P0] Helper to merge current membership
- File: `src/utils/membershipUtils.ts`
- Action: Add `mergeCurrentMembership(memberships, currentMembership)` (union, preserve current). Export if reused.
- Acceptance: No duplicates. Reusable.
- Depends on: T001
- [x] COMPLETE - Implemented in membershipUtils.ts

### T003 [P0] Dirty tracking in useMemberForm
- File: `src/hooks/useMemberForm.ts`
- Action: Track `memberDirty` (nuevoName,nuevoLastname,nuevoPhone,nuevoAddress vs initial) and `assignmentDirty` (membresia,dateInitial,multiplier,discount_percent vs initial).
- Acceptance: Correctly distinguishes domains.
- Depends on: None
- [x] COMPLETE - Implemented in useMemberForm.ts with useRef and useMemo

### T004 [P0] Submit split with recomputation gating
- File: `src/hooks/useMemberForm.ts`
- Action: If memberDirty → `updateMember` always (no assignment validation blocking). If assignmentDirty AND `canEditAssignment` (estado_pago==='pending') → `updateAsignarMemberShips` with `dateFinal = dateInitial+duration*multiplier` recalculated ONLY then. If only memberDirty → skip assignment call. Never recalc dateFinal on pure member edits.
- Acceptance: Phone-only edit doesn't change dateFinal; assignment edits recalc only when editable.
- Depends on: T003, T005
- [x] COMPLETE - Implemented in onSubmit with hasMemberChanges/hasAssignmentChanges logic

### T005 [P0] Editability logic
- File: `src/hooks/useMemberForm.ts`
- Action: `canEditAssignment = (asignacion?.estado_pago === 'pending')`. Keep personal editability independent.
- Acceptance: pending editable; paid/partial not freely editable.
- Depends on: None
- [x] COMPLETE - Implemented in useMemberForm.ts canEditAssignment memo

### T006 [P0] UI gating in MemberForm
- File: `src/pages/admin/registroPorMes/MemberForm.tsx`
- Action: When editing, NewMemberFields always enabled. Assignment/pricing gated by canEditAssignment. When not editable, read-only + operation action buttons (scaffolding).
- Acceptance: Correct gating per state.
- Depends on: T005
- [x] COMPLETE - Implemented in MemberForm.tsx with readOnly/disabled props and operation buttons

### T007 [P0] Relax editing schema
- File: `src/schemas/memberFormSchemas.ts`
- Action: Adjust `editingMemberSchema` to allow member-only validation without requiring full assignment validity when assignment not modified.
- Acceptance: Member-only passes validation.
- Depends on: T003–T004
- [x] COMPLETE - Implemented in editingMemberSchema with optional member fields

### T008 [P0] Verify build + smoke
- Action: tsc build/lint. Smoke: phone-only on pending/paid; dateFinal unchanged on member-only; pending editable, paid read-only for assignment.
- Acceptance: Builds clean, cases pass.
- Depends on: T001–T007
- [x] COMPLETE - Build passes, lint clean for changed files
## Phase 2: Operations - Suspend + mandatory reason (P1)

### T009 [P1] Backend: suspend operation
- File: `gimnasioApp/views/membership_views.py` (MembresiaAsignadaViewSet)
- Action: `@action(detail=True, methods=['post'], url_path='suspender')`. Body `{fecha_inicio?, fecha_fin?, dias?, reason}`; reason required. Multi-tenant (gimnasio). Audit log if OperationLog exists else TODO. Update end date via operation.
- Acceptance: Reason required; scoped; returns updated assignment.
- Depends on: None
- [x] COMPLETE - Implemented in membership_suspender.py with full test coverage

### T010 [P1] Frontend: Suspend modal
- File: `src/components/memberForm/operations/SuspenderMembresiaModal.tsx`
- Action: Reason required (min length), dates/days preview, validation.
- Acceptance: Validates; submits; shows errors.
- Depends on: None
- [x] COMPLETE - Implemented with SuspenderFormFields, SuspenderPreview, useSuspenderModal

### T011 [P1] Wire suspend modal
- File: `src/pages/admin/registroPorMes/MemberForm.tsx`
- Action: Wire "Suspender" when not editable (paid/partial). On success refresh, toast, close.
- Acceptance: Works; refreshes form.
- Depends on: T006,T009,T010
- [x] COMPLETE - Wired in MemberForm.tsx with SuspenderMembresiaModal

## Phase 3–4 (P2)

### T012 [P2] Backend: change-plan with credit
- File: `gimnasioApp/views/membership_views.py` (MembresiaAsignadaViewSet)
- Action: `cambiar-plan` POST, reason required. Unused-days credit, adjust dates/pricing, discount/multiplier via operation, audit, multi-tenant.
- Acceptance: Reason required; credit applied; snapshots preserved.
- Depends on: T009
- [x] COMPLETE - Implemented in membership_cambiar_plan.py and membership_calculations.py with full test coverage

### T013 [P2] Frontend: Change Plan modal
- File: `src/components/memberForm/operations/CambiarPlanModal.tsx`
- Action: New membership select, credit preview, discount/multiplier, reason required.
- Acceptance: Validates; previews; calls endpoint.
- Depends on: T012
- [x] COMPLETE - Implemented with CambiarPlanFormFields, CambiarPlanPreview, useCambiarPlanModal, and cambiarPlanUtils

### T014 [P2] Backend: refund + renew
- File: `gimnasioApp/views/membership_views.py` (MembresiaAsignadaViewSet)
- Action: `devolucion` POST `{monto,reason}` required (audit). `renovar` scaffold (prefer new assignment).
- Acceptance: Refund requires reason+amount.
- Depends on: T009
- [x] COMPLETE - Implemented in membership_devolucion.py, membership_renovar.py with full test coverage

### T015 [P2] Frontend: Refund/Renew modals
- File: `src/components/memberForm/operations/RefundModal.tsx`, `RenovarModal.tsx`
- Action: Wire buttons; validate; call endpoints.
- Acceptance: Modals work; errors handled.
- Depends on: T014
- [x] COMPLETE - Implemented with RefundFormFields, RefundPreview, useRefundModal, RenovarFormFields, RenovarPreview, useRenovarModal
