"""gimnasioApp views package — re-exports all public classes for backward compatibility."""

import logging
logger = logging.getLogger('gimnasioApp.views')

from .utils import validate_csrf, PlatformPagination
from .auth_views import (
    CookieTokenObtainPairView,
    CookieTokenRefreshView,
    CookieTokenVerifyView,
    LogoutView,
    RegisterViewSet,
    PasswordChangeView,
)
from .member_views import UserViewSet, UsuarioGymViewSet, UsuarioGymDayViewSet
from .membership_views import MembresiaViewSet, MembresiaAsignadaViewSet
from .payment_views import PagoMembresiaViewSet
from .dashboard_views import DashboardStatsView, Home, ActivitiesView, ExportReportView
from .notification_views import NotificationViewSet
from .calendar_views import TipoEventoViewSet, EventoCalendarioViewSet, PublicCalendarioView
from .platform_views import PlatformStatsView, GimnasioPlatformViewSet, DemoRequestViewSet
from .profile_views import userProfileView

__all__ = [
    'validate_csrf',
    'PlatformPagination',
    'logger',
    'CookieTokenObtainPairView',
    'CookieTokenRefreshView',
    'CookieTokenVerifyView',
    'LogoutView',
    'RegisterViewSet',
    'PasswordChangeView',
    'UserViewSet',
    'UsuarioGymViewSet',
    'UsuarioGymDayViewSet',
    'MembresiaViewSet',
    'MembresiaAsignadaViewSet',
    'PagoMembresiaViewSet',
    'DashboardStatsView',
    'Home',
    'ActivitiesView',
    'ExportReportView',
    'NotificationViewSet',
    'TipoEventoViewSet',
    'EventoCalendarioViewSet',
    'PublicCalendarioView',
    'PlatformStatsView',
    'GimnasioPlatformViewSet',
    'DemoRequestViewSet',
    'userProfileView',
]