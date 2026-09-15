# Siembra Membresias Default Specification

## Purpose

Automatically seed three default membership types (Básico, Premium, VIP) when a new gym is created, so administrators have a baseline to work with.

## Requirements

### Requirement: Auto-seed Default Memberships on Gym Creation

The system MUST create three default memberships when a new Gimnasio is created, but ONLY if the gym has no memberships yet.

#### Scenario: New gym gets default memberships

- GIVEN a new gym is created via API or signal
- WHEN the gym is saved for the first time
- THEN three memberships are automatically created:
  - Básico: duration=15, max_multiplier=1, price=0, is_active=true
  - Premium: duration=30, max_multiplier=12, price=0, is_active=true
  - VIP: duration=45, max_multiplier=8, price=0, is_active=true
- AND each membership is associated with the new gym

#### Scenario: Existing gym is not re-seeded

- GIVEN a gym that already has memberships
- WHEN the gym is updated or re-saved
- THEN no new memberships are created
- AND existing memberships are unchanged

#### Scenario: Seed respects unique_together constraint

- GIVEN a gym is being created
- WHEN the signal attempts to seed memberships
- THEN the seed only runs if no memberships exist for that gym yet
- AND if memberships already exist (e.g., from a prior step), the seed skips silently

### Requirement: Default Prices Are Zero

The system MUST set all seeded memberships to price=0. Administrators MUST edit prices manually after creation.

#### Scenario: Seeded memberships have zero price

- GIVEN a new gym is created
- WHEN the default memberships are seeded
- THEN all three memberships have price=0
- AND the administrator can later update prices via the CRUD form

### Requirement: Seed via post_save Signal

The system MUST use a Django post_save signal on Gimnasio to trigger the default membership seed.

#### Scenario: Signal fires on gym creation

- GIVEN a Gimnasio instance is saved for the first time
- WHEN the post_save signal fires
- THEN the seed function checks for existing memberships
- AND creates the three defaults if none exist

#### Scenario: Signal does not fire on updates

- GIVEN an existing Gimnasio instance
- WHEN the instance is updated and saved
- THEN the post_save signal fires but the seed function skips because memberships already exist

### Requirement: Data Migration for Existing Gyms

The system MUST include a data migration that assigns correct max_multiplier values to existing memberships based on their current name.

#### Scenario: Migration updates existing memberships

- GIVEN existing memberships with names "básico", "premium", "VIP"
- WHEN the data migration runs
- THEN "básico" memberships get max_multiplier=1
- AND "premium" memberships get max_multiplier=12
- AND "VIP" memberships get max_multiplier=8
- AND memberships with unrecognized names are left unchanged

#### Scenario: Migration is idempotent

- GIVEN the data migration has already run
- WHEN it runs again
- THEN no changes are made to memberships that already have correct max_multiplier values
