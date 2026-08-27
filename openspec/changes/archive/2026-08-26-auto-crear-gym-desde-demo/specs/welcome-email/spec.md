# Welcome Email Specification

## Purpose

Send a welcome email with credentials to the lead after gym+admin provisioning. Uses synchronous post-commit delivery with SMTP free tier.

## Requirements

### Requirement: Welcome Email Delivery

The system SHALL send a welcome email after gym+admin creation succeeds, containing the admin email, temporary password, and login link.

#### Scenario: successful email

- GIVEN gym+admin are created successfully
- WHEN post-commit email is sent
- THEN the email subject is 'Bienvenido a ControlFit — Tu gimnasio [nombre] está listo'
- AND the email body contains admin email, temporary password, and login URL
- AND the email body includes a notice that password must be changed on first login

#### Scenario: email send failure

- GIVEN gym+admin are created successfully
- WHEN post-commit email fails (SMTP error, timeout)
- THEN the gym and admin remain created (no rollback)
- AND the error is logged
- AND the response includes email_sent=False
- AND the admin can be manually notified from the admin panel

### Requirement: Temporary Password Policy

The system SHALL generate a cryptographically strong temporary password and mark the admin with must_change_password=True.

#### Scenario: temp password generation

- GIVEN admin is created for a demo lead
- WHEN password is generated
- THEN it is at least 12 characters, URL-safe
- AND must_change_password is True on the admin Usuario
