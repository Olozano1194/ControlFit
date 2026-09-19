# Test package for gimnasioApp
# This package contains refactored test modules extracted from tests.py

# Middleware tests
from .test_middleware import GimnasioMiddlewareTest

# Mixin tests
from .test_mixins import MultiTenantViewSetMixinTest

# View tests
from .test_views import UserViewSetCreateTest

# Storage tests
from .test_storage import SupabaseMediaStorageTest, UsuarioSerializerAvatarTest

# Integration avatar tests
from .test_integration_avatar import AvatarUploadIntegrationTest

# Payment tests
from .test_payments import (
    MembresiaAsignadaSaveTest,
    PagoMembresiaValidacionTest,
    MembresiaAsignadaPropiedadesTest,
    PagoMembresiaIntegracionTest,
)

# Home dashboard tests
from .test_home_dashboard import HomeDashboardPagosTest

# Membership model tests
from .test_membership_models import (
    MembresiaModelTest,
    MembresiaAsignadaModelSaveTest,
    SeedDefaultMembershipsTest,
)

# Serializer tests
from .test_serializers import (
    MembresiasSerializerTest,
    MembresiaAsignadaSerializerValidationTest,
)

# Email tests
from .test_email import EmailServiceTest

# JWT token tests
from .test_jwt_token import TokenLifetimeSettingsTest

# CSRF cookie tests
from .test_csrf_cookie import CSRFSettingTest, CSRFCookieHelperTest

# CSRF validation tests
from .test_csrf_validation import CSRFValidationTest

# Auth CSRF tests
from .test_auth_csrf import AuthViewsCSRFCookieTest

# Token verify tests
from .test_token_verify import (
    TokenVerifyEndpointTest,
    TokenVerifyIntegrationTest,
)

# CSRF enforcement tests
from .test_csrf_enforcement import (
    CSRFEnforcementIntegrationTest,
    FullAuthFlowIntegrationTest,
)

__all__ = [
    "GimnasioMiddlewareTest",
    "MultiTenantViewSetMixinTest",
    "UserViewSetCreateTest",
    "SupabaseMediaStorageTest",
    "UsuarioSerializerAvatarTest",
    "AvatarUploadIntegrationTest",
    "MembresiaAsignadaSaveTest",
    "PagoMembresiaValidacionTest",
    "MembresiaAsignadaPropiedadesTest",
    "PagoMembresiaIntegracionTest",
    "HomeDashboardPagosTest",
    "MembresiaModelTest",
    "MembresiaAsignadaModelSaveTest",
    "SeedDefaultMembershipsTest",
    "MembresiasSerializerTest",
    "MembresiaAsignadaSerializerValidationTest",
    "EmailServiceTest",
    "TokenLifetimeSettingsTest",
    "CSRFSettingTest",
    "CSRFCookieHelperTest",
    "CSRFValidationTest",
    "AuthViewsCSRFCookieTest",
    "TokenVerifyEndpointTest",
    "TokenVerifyIntegrationTest",
    "CSRFEnforcementIntegrationTest",
    "FullAuthFlowIntegrationTest",
]