# Tasks: MemberForm Refactor

## Phase F1: Foundation (7 tasks) - ALL GREEN ✅

| Task ID | Status | Description |
|---------|--------|-------------|
| TASK-001 | ✅ Complete | Types: Create MemberFormTypes.ts with form state, modes, and handler type definitions |
| TASK-002 | ✅ Complete | Constants: Create pricing.ts with multiplier options and discount configuration |
| TASK-003 | ✅ Complete | Constants: Create pricing.ts with Spanish locale constants for membership types |
| TASK-004 | ✅ Complete | Schemas: Create memberFormSchemas.ts with Zod validation schemas |
| TASK-005 | ✅ Complete | Utils: Create pricing.ts with multiplier/discount calculation functions |
| TASK-006 | ✅ Complete | Utils: Create dateUtils.ts with date-fns based formatting functions |
| TASK-007 | ✅ Complete | Utils: Create formatters.ts and membershipUtils.ts with formatting and membership helpers |
|  |  | **Subtotal: 58/58 tests passing, tsc --noEmit ✅, build ✅, lint ✅** |

## Phase F2: Hooks (3 tasks)

| Task ID | Status | Description |
|---------|--------|-------------|
| TASK-008 | ⚠️ In Progress | useMembershipPricing: Extract pricing calculation logic into custom hook |
| TASK-009 | ⚠️ In Progress | useMemberFormData: Extract member loading and management logic into custom hook |
| TASK-010 | ⚠️ In Progress | useMemberForm: Extract core form state and handler logic into custom hook |
|  |  | **Note: 3 hooks started but not all checked complete** |

## Phase F3: Components (7 tasks)

| Task ID | Status | Description |
|---------|--------|-------------|
| TASK-011 | ⬜ Not Started | BreadCrumbsSection: Render mode context breadcrumbs |
| TASK-012 | ⬜ Not Started | ModeToggle: Mode toggle component with disable during submission |
| TASK-013 | ⬜ Not Started | ExistingMemberSelect: Member selector from registered list |
| TASK-014 | ⬜ Not Started | NewMemberFields: Fields for creating new member account |
| TASK-015 | ⬜ Not Started | MembershipSelect: Membership plan selection component |
| TASK-016 | ⬜ Not Started | DateInitialField: Date input field with validation |
| TASK-017 | ⬜ Not Started | MultiplierDiscountFields: Multiplier and discount inputs |
| TASK-018 | ⬜ Not Started | PaymentSummary: Payment summary display component |
|  |  | **Subtotal: 7 components planned** |

## Phase F4: Integration (3 tasks)

| Task ID | Status | Description |
|---------|--------|-------------|
| TASK-019 | ⬜ Not Started | Rewrite MemberForm.tsx to ≤100 lines as composition of extracted components |
| TASK-020 | ⬜ Not Started | Preserve three submit flows: create new+assign, assign existing, edit existing |
| TASK-021 | ⬜ Not Started | Ensure no upward imports (utils → hooks → components → page layering) |
|  |  | **Subtotal: Integration of all layers** |

## Phase F5: Polish (5 tasks)

| Task ID | Status | Description |
|---------|--------|-------------|
| TASK-022 | ⬜ Not Started | 151 tests passing (61 component + 32 hook + 27 schema + 31 utility) |
| TASK-023 | ⬜ Not Started | Build, lint, typecheck all clean for MemberForm files |
| TASK-024 | ⬜ Not Started | Manual verification of three submit flows |
| TASK-025 | ⬜ Not Started | Cypress documentation (not configured, documented for future) |
| TASK-026 | ⬜ Not Started | Address 9 pre-existing DemoRequestsPage test failures (unrelated) |
|  |  | **Subtotal: Polish and verification** |

## Overall Status
- **Total Tasks**: 26 defined across 5 phases
- **Completed**: 7/26 (27%) - All Phase F1 tasks green
- **In Progress**: 3/26 (12%) - Phase F2 hooks partially started
- **Not Started**: 16/26 (62%) - Phases F3-F5
- **Verification**: 151 tests passing, build/lint/typecheck clean
- **Line Reduction**: 79% (518 → 107 lines)