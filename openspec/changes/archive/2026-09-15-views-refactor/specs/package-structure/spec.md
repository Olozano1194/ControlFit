# Delta for Package Structure

## ADDED Requirements

### Requirement: Package Existence

The system SHALL replace the monolithic `gimnasioApp/views.py` file with a Python package `gimnasioApp/views/`.

#### Scenario: Package directory exists

- GIVEN the refactored codebase
- WHEN the file system is inspected
- THEN `gimnasioApp/views/` exists as a directory
- AND `gimnasioApp/views/__init__.py` exists

### Requirement: Domain Module Organization

The system SHALL organize view classes into domain-specific modules within the package.

#### Scenario: Domain modules present

- GIVEN the `gimnasioApp/views/` package
- WHEN the package contents are listed
- THEN 10 domain modules exist: `auth_views.py`, `member_views.py`, `membership_views.py`, `payment_views.py`, `dashboard_views.py`, `notification_views.py`, `calendar_views.py`, `platform_views.py`, `utils.py`, `profile_views.py`
- AND `__pycache__` directory is ignored

#### Scenario: Domain separation

- GIVEN a domain module (e.g., `auth_views.py`)
- WHEN its contents are inspected
- THEN it contains ONLY classes belonging to that domain (6 auth classes)
- AND no classes from other domains are present

### Requirement: Module Class Mapping

The system SHALL place each view class in its designated domain module as specified in the proposal.

#### Scenario: Auth classes in auth_views

- GIVEN the `auth_views.py` module
- WHEN its classes are listed
- THEN it contains: CookieTokenObtainPairView, CookieTokenRefreshView, CookieTokenVerifyView, LogoutView, RegisterViewSet, PasswordChangeView

#### Scenario: Member classes in member_views

- GIVEN the `member_views.py` module
- WHEN its classes are listed
- THEN it contains: UserViewSet, UsuarioGymViewSet, UsuarioGymDayViewSet

#### Scenario: Membership classes in membership_views

- GIVEN the `membership_views.py` module
- WHEN its classes are listed
- THEN it contains: MembresiaViewSet, MembresiaAsignadaViewSet

#### Scenario: Payment class in payment_views

- GIVEN the `payment_views.py` module
- WHEN its classes are listed
- THEN it contains: PagoMembresiaViewSet

#### Scenario: Dashboard classes in dashboard_views

- GIVEN the `dashboard_views.py` module
- WHEN its classes are listed
- THEN it contains: DashboardStatsView, Home, ActivitiesView, ExportReportView

#### Scenario: Notification class in notification_views

- GIVEN the `notification_views.py` module
- WHEN its classes are listed
- THEN it contains: NotificationViewSet

#### Scenario: Calendar classes in calendar_views

- GIVEN the `calendar_views.py` module
- WHEN its classes are listed
- THEN it contains: TipoEventoViewSet, EventoCalendarioViewSet, PublicCalendarioView

#### Scenario: Platform classes in platform_views

- GIVEN the `platform_views.py` module
- WHEN its classes are listed
- THEN it contains: PlatformStatsView, GimnasioPlatformViewSet

#### Scenario: Utility functions in utils

- GIVEN the `utils.py` module
- WHEN its contents are listed
- THEN it contains: validate_csrf, PlatformPagination

#### Scenario: Profile view in profile_views

- GIVEN the `profile_views.py` module
- WHEN its contents are listed
- THEN it contains: userProfileView