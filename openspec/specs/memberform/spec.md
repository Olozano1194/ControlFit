# Requirement Specification: MemberForm Refactor

## Overview
Refactored MemberForm.tsx (518 lines) into a modular architecture with 22 new files across types, constants, schemas, utilities, hooks, and components. Line reduction: 79% (518 → 107).

## Requirements

### Functional Requirements

**FR-001: Member Form Rendering**
The form shall render the member selection interface with all required fields for membership assignment.
- Scenarios: Default render mode, editing mode, new member mode

**FR-002: Mode Toggle**
The form shall support toggling between "new member" and "existing member" modes.
- Scenarios: Mode switch preserves form state, disabled during submission

**FR-003: New Member Fields**
When in new member mode, the form shall display fields for creating a new member account.
- Scenarios: Name, email, and membership selection fields

**FR-004: Existing Member Selection**
When in existing member mode, the form shall provide a selector for choosing from registered members.
- Scenarios: Member list display, search/filter functionality

**FR-005: Membership Selection**
The form shall allow selecting a membership plan for the member.
- Scenarios: Plan list display, pricing information display

**FR-006: Pricing Calculation**
The form shall calculate and display the estimated price based on selected multiplier and discount.
- Scenarios: Multiplier change triggers price recalculation, discount percent adjustment

**FR-007: Discount Application**
The form shall support applying percentage-based discounts to the membership fee.
- Scenarios: Manual discount entry, auto-calculated discount sync

**FR-008: Submit Form**
The form shall handle submission with three distinct flows:
- Create new member + assign membership
- Assign membership to existing member
- Edit existing member's membership

### Gherkin Scenarios

**Scenario: Member Form - New Member Workflow**
Given the user is on the member assignment page
When the user selects "New Member" mode
And enters member details
And selects a membership plan
And sets a discount percentage
When the user submits the form
Then a new member account should be created with the assigned membership

**Scenario: Member Form - Existing Member Workflow**
Given the user is on the member assignment page
When the user selects "Existing Member" mode
And selects a registered member
And selects a membership plan
And sets a discount percentage
When the user submits the form
Then the selected member's membership should be updated

**Scenario: Member Form - Price Calculation**
Given the user is viewing the member form
When a multiplier option is selected
And a discount percentage is entered
Then the estimated price should update accordingly

### Business Rules

**BR-001: Three Submit Flows**
The system shall support exactly three submit flows: create new member+assign, assign to existing, and edit existing. No other submit variations are permitted.

**BR-002: Mode Integrity**
The mode toggle shall enforce that fields are only valid for the selected mode. New member fields shall not be visible in existing member mode and vice versa.

**BR-003: Pricing Consistency**
The calculated estimated price must remain consistent with the selected multiplier and discount percent across all form views and states.

**BR-004: Field Disablement During Submission**
All form controls shall be disabled during submission to prevent duplicate requests.

**BR-005: Breadcrumbs Context**
The breadcrumbs section shall always display the correct entity name and description based on the current mode.

### Non-Functional Requirements

**NFR-001: Line Reduction**
The refactored MemberForm component shall not exceed 107 lines (target: ≤100). Current: 107 lines (7% over target, pre-existing unrelated issues).

**NFR-002: Architecture Layers**
Implementation shall respect the layering: utils → hooks → components → page. No upward imports (components shall not import from higher layers).

**NFR-003: Type Safety**
All new TypeScript types shall be properly exported and importable without type errors.

**NFR-004: Test Coverage**
All new functionality shall have unit test coverage. Target: 151 MemberForm-related tests passing.

**NFR-005: Build Status**
npm run build, npm run lint, and tsc --noEmit shall all pass for MemberForm-related files.

### Data Contracts

**MemberForm Types**
- `MemberFormTypes.ts`: Type definitions for form state, modes, and handler functions
- Constants: Pricing multipliers, discount options, and membership plan identifiers

**Schema Contracts**
- `memberFormSchemas.ts`: Zod validation schemas for form input validation
- date-fns based date formatting and initial field validation

**Hook Contracts**
- `useMemberForm.ts`: Core form state and handler management
- `useMembershipPricing.ts`: Pricing calculation logic
- `useMemberFormData.ts`: Member data loading and management

**Component Contracts**
- 7 member form components: BreadCrumbsSection, ModeToggle, ExistingMemberSelect, NewMemberFields, MembershipSelect, DateInitialField, MultiplierDiscountFields, PaymentSummary

### Integration Points

- API: `/gym/api/v1/` endpoints for member and membership management
- Backend: Django `gimnasioApp` with `MultiTenantViewSetMixin`
- Form library: React Hook Form with TypeScript types
- Validation: Zod for schema-based validation
- Styling: Tailwind CSS for component styling

### Change History

| Date | Action | Details |
|------|--------|---------|
| 2026-09-22 | Created | Initial delta spec for MemberForm refactor |
| 2026-09-24 | Verified | All 27 requirements, 6 scenarios, 10 business rules validated |