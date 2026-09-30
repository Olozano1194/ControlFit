# Design: MemberForm Refactor

## Architecture Layers

### utils Layer
Pure functions without React dependencies:

- `pricing.ts`: Multiplier calculations, discount percent computations, estimated price derivation
- `dateUtils.ts`: date-fns based date formatting, initial field date processing
- `formatters.ts`: String formatting for display (currency, percentages, dates)
- `membershipUtils.ts`: Membership plan calculations, plan identifier utilities

### hooks Layer
Custom React hooks consuming utils and providing stateful logic:

- `useMemberForm.ts`: Core form state (modo, register, errors, isSubmitting), handler functions (handleSubmit, handleMemberShipsChange, handleMultiplierChange, setDiscountPercent), form data (miembros, membresias, selectedMembresia)
- `useMembershipPricing.ts`: Pricing calculation logic, multiplier options, discount percent state, estimated price and estimated date final computation
- `useMemberFormData.ts`: Member loading from API, member list management, selected member state

### components Layer
Presentational UI components consuming hooks and utils:

- `BreadCrumbsSection`: Displays breadcrumbs with mode context (isEditing, title, description)
- `ModeToggle`: Switch between "New Member" and "Existing Member" modes, disabled during submission
- `ExistingMemberSelect`: Dropdown/selector for registered members, with register prop, errors, and disabled state
- `NewMemberFields`: Fields for creating a new member (name, email, etc.)
- `MembershipSelect`: Plan selection component with onChange handler
- `DateInitialField`: Date input field with error handling and disabled state
- `MultiplierDiscountFields`: Multiplier selection and discount percent input with change handlers
- `PaymentSummary`: Summary display of selected membership, multiplier, discount, estimated price, and total days

### page Layer
- `MemberForm.tsx`: Final refactored component (107 lines) that composes all lower layers
  - Imports only from hooks and components (no upward imports)
  - Uses useMemberForm hook for all form state
  - Renders component composition with conditional rendering for mode flows
  - Preserves three submit flows: create new+assign, assign existing, edit existing

## State Management

### Form State (useMemberForm hook)
- `modo`: "new" | "existing" string state
- `setModo`: Mode toggle function
- `register`: React Hook Form register function
- `handleSubmit`: Form submission handler
- `errors`: Validation error state
- `isSubmitting`: Submission in-progress flag
- `miembros`: Array of registered members (existing mode)
- `membresias`: Array of available membership plans
- `selectedMembresia`: Currently selected membership plan
- `multiplier`: Selected multiplier value
- `discountPercent`: Discount percentage value
- `multiplierOptions`: Available multiplier options
- `showMultiplier`: Boolean flag for displaying multiplier fields
- `estimatedPrice`: Calculated estimated price
- `totalDays`: Total days calculation
- `estimatedDateFinal`: Final estimated date

### API Integration
- Member data loaded via useMemberFormData hook
- Membership plans fetched from `/gym/api/v1/` endpoints
- Multi-tenant scoping via `request.gimnasio` middleware

## Component Hierarchy

```
MemberForm (page)
├── BreadCrumbsSection
├── form
│   ├── ModeToggle
│   ├── {ExistingMemberSelect | NewMemberFields}
│   ├── section (grid layout)
│   │   ├── MembershipSelect
│   │   └── DateInitialField
│   ├── {MultiplierDiscountFields} (conditional: showMultiplier)
│   └── PaymentSummary
└── Button (submit)
```

## Validation Strategy

### Zod Schemas (memberFormSchemas.ts)
- Member name validation (required, min/max length)
- Email validation (format check)
- Membership plan selection validation
- Discount percent range validation (0-100)
- Multiplier option validation

### Runtime Validation
- Validation errors displayed inline next to respective fields
- Form disabled during submission
- submit prevented on validation errors

## Testing Strategy

### Unit Tests (151 total)
- 61 component tests: Each of the 7+ components tested with various props and states
- 32 hook tests: useMemberForm, useMembershipPricing, useMemberFormData scenarios
- 27 schema tests: Zod schema validation edge cases
- 31 utility tests: pricing calculations, date formatting, membership utilities

### Test Organization
- Component tests render full MemberForm and individual components
- Hook tests verify state management and side effects
- Schema tests verify validation edge cases
- Utility tests verify pure function outputs

## Implementation Phases (from SDD tasks)

### Phase F1 Foundation
- Types, constants, schemas, 4 utils
- All green: 58/58 tests passing, tsc ✅, build ✅, lint ✅

### Phase F2 Hooks
- useMembershipPricing, useMemberFormData, useMemberForm
- In progress at archive time

### Phase F3 Components
- 7 sub-components (BreadCrumbsSection, ModeToggle, etc.)
- Not started at archive time

### Phase F4 Integration
- MemberForm.tsx rewrite ≤100 lines
- Not started at archive time

### Phase F5 Polish
- Tests, CI, manual 3-flow verification
- Not started at archive time

## Multi-Tenant Considerations
All new types and hooks must carry `gimnasio` FK scoping where applicable. The MultiTenantViewSetMixin pattern should be respected in any API integrations.