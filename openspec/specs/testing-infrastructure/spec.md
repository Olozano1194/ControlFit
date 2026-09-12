# Testing Infrastructure Specification

## Purpose

Configure Django test runner to use SQLite in-memory database for fast local test execution and CI pipeline without MySQL dependency.

## Requirements

### Requirement: SQLite Test Database Configuration

The system SHALL configure Django test runner to use SQLite in-memory database when `TEST` setting is present. The `DATABASES['default']['TEST']` SHALL contain `{'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}`. This configuration SHALL be used only for tests, not for development or production.

#### Scenario: Test runner uses SQLite in-memory

- GIVEN the Django settings with `TEST` configuration for SQLite
- WHEN running `python manage.py test`
- THEN the test database is SQLite in-memory
- AND tests complete in <10 seconds locally

#### Scenario: Development uses original database

- GIVEN the Django settings with `TEST` configuration
- WHEN running the development server
- THEN the development database is PostgreSQL (or configured database)
- AND SQLite is not used

### Requirement: CI Pipeline Without MySQL

The system SHALL provide GitHub Actions workflow that runs tests without MySQL service. The workflow SHALL use `ubuntu-latest` with default SQLite. The workflow SHALL NOT require MySQL service container.

#### Scenario: CI runs tests on SQLite

- GIVEN a GitHub Actions workflow with `ubuntu-latest`
- WHEN the workflow runs `python manage.py test`
- THEN tests execute against SQLite in-memory database
- AND no MySQL service is started

#### Scenario: CI passes without MySQL configuration

- GIVEN the GitHub Actions workflow
- WHEN the workflow runs
- THEN there are no MySQL connection errors
- AND all tests pass

### Requirement: Test Performance Baseline

The system SHALL ensure test suite completes in <10 seconds locally. This performance target SHALL be validated by running `python manage.py test` and measuring execution time.

#### Scenario: Local test performance

- GIVEN a developer running tests locally
- WHEN executing `python manage.py test`
- THEN the test suite completes in <10 seconds
- AND no database connection timeouts occur

### Requirement: Migration Compatibility

The system SHALL ensure SQLite test database supports all Django migrations. Migrations SHALL run successfully against SQLite in-memory database without errors.

#### Scenario: Migrations run on SQLite

- GIVEN the SQLite test database
- WHEN running `python manage.py migrate`
- THEN all migrations complete successfully
- AND no SQLite-specific errors occur

## Test Requirements

### Unit Tests

- Test that `DATABASES['default']['TEST']` contains correct SQLite configuration
- Test that test runner uses SQLite engine when `TEST` setting is present
- Test that development server uses original database configuration

### Integration Tests

- Test full test suite runs against SQLite in-memory database
- Test migrations complete successfully on SQLite
- Test performance benchmark (<10 seconds)

### E2E Tests

- Test CI workflow runs without MySQL service
- Test CI passes with SQLite test database