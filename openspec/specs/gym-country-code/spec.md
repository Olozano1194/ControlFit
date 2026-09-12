# Gym Country Code Specification

## Purpose

Make WhatsApp country code configurable per gym, allowing internationalization of WhatsApp links without hardcoded prefixes.

## Requirements

### Requirement: Country Code Field

The system SHALL add a `country_code` field to the `Gimnasio` model. The field SHALL be a `CharField(max_length=5, default='57')` to support country codes like '57' (Colombia), '1' (USA), '52' (Mexico), etc.

#### Scenario: Default country code is '57'

- GIVEN a new Gimnasio instance
- WHEN creating without specifying `country_code`
- THEN `country_code` defaults to '57'
- AND WhatsApp links use prefix '57'

#### Scenario: Custom country code preserved

- GIVEN a Gimnasio with `country_code='1'`
- WHEN saving the instance
- THEN `country_code` is stored as '1'
- AND WhatsApp links use prefix '1'

### Requirement: Migration with Default

The system SHALL generate a migration that adds the `country_code` field with default '57'. Existing records SHALL receive the default value.

#### Scenario: Migration adds field

- GIVEN existing Gimnasio records
- WHEN running migrations
- THEN the `country_code` field is added
- AND all existing records have `country_code='57'`

#### Scenario: Migration is reversible

- GIVEN the migration adding `country_code`
- WHEN rolling back the migration
- THEN the field is removed
- AND existing data is preserved

### Requirement: Configurable WhatsApp Links

The system SHALL update `NotificationManager._construir_whatsapp_link()` to use `gimnasio.country_code` instead of hardcoded `PREFIJO_WHATSAPP`. The method SHALL accept the gym instance or country code as parameter.

#### Scenario: WhatsApp link uses gym country code

- GIVEN a gym with `country_code='1'`
- WHEN generating a WhatsApp link for a member
- THEN the link uses prefix '1'
- AND the link format is `https://wa.me/1{phone}?text={message}`

#### Scenario: Default country code used when not set

- GIVEN a gym without `country_code` (or None)
- WHEN generating a WhatsApp link
- THEN the default '57' is used
- AND the link uses prefix '57'

### Requirement: Backward Compatibility

The system SHALL maintain backward compatibility. Existing functionality SHALL not break. The default '57' preserves current behavior for Colombian gyms.

#### Scenario: Existing behavior preserved

- GIVEN a gym with default `country_code='57'`
- WHEN generating WhatsApp links
- THEN behavior is identical to current hardcoded '57'
- AND no changes in link format

#### Scenario: No breaking changes

- GIVEN the migration and code changes
- WHEN deploying the update
- THEN existing WhatsApp links continue to work
- AND no frontend changes required

## Test Requirements

### Unit Tests

- Test `Gimnasio.country_code` defaults to '57'
- Test `Gimnasio.country_code` can be set to custom value
- Test `_construir_whatsapp_link` uses gym country code
- Test `_construir_whatsapp_link` uses default when country code missing

### Integration Tests

- Test migration applies successfully with default
- Test existing records get default '57'
- Test WhatsApp links generated with correct prefix

### E2E Tests

- Test full notification flow with custom country code
- Test WhatsApp link opens correct international number