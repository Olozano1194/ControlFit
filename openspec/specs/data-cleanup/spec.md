# Data Cleanup Specification

## Purpose

Remove deprecated `notified_at` column from `MembresiaAsignada` model to eliminate dead code and reduce schema complexity.

## Requirements

### Requirement: Remove notified_at Field

The system SHALL remove the `notified_at` field from the `MembresiaAsignada` model. The field is deprecated and no longer used for notification logic (replaced by `Notification` model).

#### Scenario: Field removed from model

- GIVEN the `MembresiaAsignada` model
- WHEN the model is defined
- THEN the `notified_at` field is NOT present
- AND the model has no reference to `notified_at`

#### Scenario: Database migration removes column

- GIVEN a database with existing `notified_at` column
- WHEN running migrations
- THEN the column is removed from the database table
- AND existing data is preserved (column dropped, not table)

### Requirement: No Code References

The system SHALL have no code references to `notified_at` after removal. All references in views, serializers, tests, and admin SHALL be removed or updated.

#### Scenario: Grep finds no references

- GIVEN the codebase after removing `notified_at`
- WHEN searching for `notified_at` across all files
- THEN no matches are found
- OR only documentation references remain (help_text, comments)

#### Scenario: Tests pass without notified_at

- GIVEN the test suite
- WHEN running `python manage.py test`
- THEN all tests pass
- AND no tests reference `notified_at`

### Requirement: Migration Safety

The system SHALL generate a `RemoveField` migration that safely removes the column. The migration SHALL be reversible for rollback purposes.

#### Scenario: Migration generated correctly

- GIVEN the model change
- WHEN running `python makemigrations`
- THEN a `RemoveField` migration is generated
- AND the migration targets `MembresiaAsignada.notified_at`

#### Scenario: Migration applies successfully

- GIVEN the generated migration
- WHEN running `python migrate`
- THEN the migration applies without errors
- AND the column is removed from the database

### Requirement: Notification Model Unaffected

The system SHALL ensure the `Notification` model is unaffected by this change. The `Notification` model is the replacement for `notified_at` and SHALL continue to work correctly.

#### Scenario: Notification model unchanged

- GIVEN the `Notification` model
- WHEN the `notified_at` field is removed from `MembresiaAsignada`
- THEN the `Notification` model is unchanged
- AND notification generation continues to work

## Test Requirements

### Unit Tests

- Test `MembresiaAsignada` model does not have `notified_at` attribute
- Test `MembresiaAsignada` instances cannot be created with `notified_at`
- Test migration applies successfully

### Integration Tests

- Test existing `MembresiaAsignada` records are preserved after migration
- Test `Notification` model continues to generate notifications
- Test no code references to `notified_at` remain

### E2E Tests

- Test full test suite passes after column removal
- Test no regressions in membership assignment flow