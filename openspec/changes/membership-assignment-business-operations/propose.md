# Change Proposal: membership-assignment-business-operations

## What

Separate member personal data editing from membership assignment editing. Make personal data (name, lastname, phone, address) **always editable** in any state. Replace free-form editing of assignment fields (membership, dates, multiplier, discount) with **explicit business operations** (suspend, refund, change plan mid-period, renew) when financial state exists (`paid`/`partial`/`pending`), while keeping a safe path for non-financial corrections where appropriate. Fix `filterActiveMemberships` so it doesn't block saving member personal data when a plan was deactivated after sale.

## Why

The current MemberForm mixes two domains (member vs assignment/accounting). When editing an assignment, `onSubmit` recalculates `dateFinal = dateInitial + duration*multiplier` on every save (even if only phone changed), risking accidental mutation of the membership end date. The rule `isMembershipActive = (dateFinal>=today AND estado_pago !== 'paid')` blocks legitimate cases (active+paid memberships that need suspensions/extensions for maintenance/illness). Also `filterActiveMemberships` (shows only `is_active===true`) can prevent saving personal data if the original plan is deactivated. The assignment stores accounting snapshots (`price`, `total_pagado`, `saldo_pendiente`, `estado_pago`) — mutations must be auditable (who/why/when) to avoid corrupting financial history. Business operations (append-only) preserve audit trail and support the 5 required scenarios safely.

## Scenarios

1. Gym closed/maintenance → recover days (suspension with reason/dates)
2. Member ill → recover days/extension (suspension)
3. Refund → record properly (refund operation with amount/reason)
4. Change plan mid-period → without breaking accounting (plan change with unused-days credit)
5. Edit personal data (name/lastname/phone/address) → always allowed
## Scope

**In scope:**
- Redefine edit rules in MemberForm (separate domains): personal data always editable; assignment editable only via operations when financially relevant.
- Fix `filterActiveMemberships` behavior so personal data updates aren't blocked when selected membership is unavailable/inactive.
- Adjust schema/UX: when editing, allow member fields unconditionally; for assignment/pricing, hide free edit when assignment has payments/state (`paid`/`partial`) and offer operation actions/modals instead.
- Identify minimal API surface needed for operations and document gaps.

**Out of scope:**
- Full backend implementation of all new operations if missing (inventory gaps only).
- Payment collection UI beyond existing.
## Affected Areas

- `src/hooks/useMemberForm.ts` — `onSubmit` (avoid silent dateFinal recomputation on pure personal-data edits), `isMembershipActive`/editability logic
- `src/pages/admin/registroPorMes/MemberForm.tsx` — UI separation (personal section always enabled, assignment/pricing gating)
- `src/schemas/memberFormSchemas.ts` — `editingMemberSchema`
- `src/hooks/useMemberFormData.ts` — `filterActiveMemberships` usage
- `src/utils/membershipUtils.ts` — filter semantics
- `src/model/asignarMemberShips.model.ts`, `src/model/dto/asignarMemberShips.dto.ts`, `src/api/action/asignarMemberShips.api.ts`, `src/api/action/userGym.api.ts`

## Approaches

**A. Guarded free edit**: Split submit (updateMember always, updateAssignment only if assignment fields dirty). Quick but weaker audit.
**B. Immutable + full operations**: Strongest correctness/audit, highest effort.
**C. Hybrid (recommended)**: Personal always editable. Assignment: block free edit when `paid`/`partial`; allow operations for paid cases, careful edits for pending.

## Risks

- Accounting integrity (silent dateFinal recomputation)
- filterActiveMemberships blocks unrelated updates
- UX needs clear operations UI
- Backend gaps for operations endpoints

## Recommendation

**Option C (Hybrid)**. Fix blockers first (domain split, filter, recomputation gating), introduce operations incrementally.

## Open Questions

1. States allowing suspend/extend? (active+paid, active+partial, or paid only?)
2. Reason mandatory for suspensions/refunds/plan changes?
3. Plan change with unused-days credit in MVP, or only suspensions first?
4. Move discount/multiplier to operations?
5. Decouple personal data into separate form/section?

## Next Steps

1. SDD Spec with requirements
2. SDD Design (operations API + UI state + gating rules)
3. SDD Tasks split into units
4. Clarify open questions
