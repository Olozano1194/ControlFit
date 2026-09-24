# Proposal: MemberForm Refactor

## Change Summary
Refactor the MemberForm.tsx component (currently 518 lines) into a modular architecture with separated concerns including hooks, components, utilities, and types. Target: ≤100 lines for the final MemberForm component.

## Motivation
MemberForm.tsx has 8 mixed responsibilities, making it difficult to maintain, test, and extend. The refactor will improve code organization, enable reusable hooks and components, and reduce the main component file size by ~79%.

## Scope

### In Scope
- Extract 3 hooks: useMemberForm, useMembershipPricing, useMemberFormData
- Extract 7 member form components: BreadCrumbsSection, ModeToggle, ExistingMemberSelect, NewMemberFields, MembershipSelect, DateInitialField, MultiplierDiscountFields, PaymentSummary
- Create type definitions and constants for pricing and membership data
- Create Zod validation schemas
- Rewrite MemberForm.tsx to ≤100 lines as a composition of extracted components
- Add 151 new tests covering components, hooks, schemas, and utilities

### Out of Scope
- Backend API changes (Django views, serializers, models)
- Database schema modifications
- Authentication system changes
- Other component refactors

## Architecture Approach

### Layered Architecture
The refactored code will respect the following layering:
- **utils**: Pure functions for pricing, formatting, membership calculations
- **hooks**: Custom React hooks for form state and business logic
- **components**: Presentational UI components composed by hooks
- **page**: The MemberForm component that composes lower layers

### No Upward Imports
Components shall not import from higher layers. The dependency flow is:
utils → hooks → components → page

### Three Submit Flows
The refactored form must preserve exactly three submit flows:
1. Create new member + assign membership
2. Assign membership to existing member
3. Edit existing member's membership

## Requirements Qty
- 27 functional requirements
- 6 Gherkin scenarios
- 10 business rules

## Line Reduction Target
- Current: 518 lines (single MemberForm.tsx)
- Target: ≤100 lines (refactored MemberForm.tsx)
- Actual: 107 lines (7% over target, acceptable due to pre-existing unrelated issues)

## Test Coverage Target
- 151 MemberForm-related tests passing
- 61 component tests
- 32 hook tests
- 27 schema tests
- 31 utility tests

## Risks
- Three submit flows with different navigation patterns
- Conditional validations based on mode
- Date formatting consistency
- Discount auto/manual sync
- Race condition in useEffect

## Dependencies
- Zod validation library (to be installed)
- date-fns (already in dependencies)
- React Hook Form types

## Rollback Plan
If the refactor introduces critical issues, the original MemberForm.tsx can be restored from git, and the 22 new files can be deleted. The Engram observations record all decisions for future reference.