# Membresia Personalizable Specification

## Purpose

Allow each gym to define its own membership types with custom names, durations, prices, and multiplier limits. Replaces the rigid `choices` field with a free-text approach.

## Requirements

### Requirement: Custom Membership Creation

The system MUST allow gym administrators to create membership types with a free-text name, duration (1–365 days), price, max_multiplier, and is_active toggle.

#### Scenario: Create a new membership

- GIVEN a logged-in gym administrator
- WHEN they submit a membership with name="Mensual $50k", duration=30, max_multiplier=6, price=50000
- THEN the membership is created and associated with their gym
- AND is_active defaults to true

#### Scenario: Name uniqueness per gym

- GIVEN a gym already has a membership named "Premium"
- WHEN they attempt to create another membership named "Premium" for the same gym
- THEN the system rejects the request with a uniqueness violation error

#### Scenario: Different gyms can share the same name

- GIVEN gym A has a membership named "Básico"
- WHEN gym B creates a membership named "Básico"
- THEN both memberships are created successfully

### Requirement: Membership Duration Validation

The system MUST validate that membership duration is between 1 and 365 days.

#### Scenario: Valid duration

- GIVEN a gym administrator creating a membership
- WHEN they set duration=30
- THEN the membership is created successfully

#### Scenario: Duration out of range

- GIVEN a gym administrator creating a membership
- WHEN they set duration=0 or duration=400
- THEN the system rejects the request with a validation error

### Requirement: Max Multiplier Controls Assignment

The system MUST use max_multiplier to limit how many times a membership can be multiplied when assigned to a client.

#### Scenario: Single-use membership (max_multiplier=1)

- GIVEN a membership with max_multiplier=1
- WHEN a client is assigned this membership
- THEN multiplier MUST be exactly 1
- AND the frontend hides or disables the multiplier input

#### Scenario: Multipliable membership

- GIVEN a membership with max_multiplier=12
- WHEN a client is assigned this membership with multiplier=6
- THEN the assignment is accepted

#### Scenario: Multiplier exceeds max

- GIVEN a membership with max_multiplier=4
- WHEN an assignment is submitted with multiplier=5
- THEN the system rejects the assignment with a validation error

### Requirement: Membership CRUD Operations

The system MUST support full CRUD operations on memberships via API endpoints.

#### Scenario: List memberships

- GIVEN a gym administrator
- WHEN they request the memberships list
- THEN all memberships for their gym are returned

#### Scenario: Update membership

- GIVEN a gym administrator
- WHEN they update a membership's price or duration
- THEN the changes are persisted and reflected in subsequent reads

#### Scenario: Deactivate membership

- GIVEN a gym administrator
- WHEN they toggle is_active to false
- THEN the membership is no longer available for new assignments
- AND existing active assignments are unaffected

### Requirement: Frontend Form for Membership Management

The system MUST provide a frontend form using text input for name, number inputs for duration and max_multiplier, and a toggle for is_active.

#### Scenario: Form displays correct fields

- GIVEN an administrator navigates to the membership form
- THEN they see a text input for name, number inputs for duration (1–365) and max_multiplier (≥1), and an is_active toggle

#### Scenario: Form validation feedback

- GIVEN an administrator submits the form with duration=500
- THEN the form displays a validation error before submission
