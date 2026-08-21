from django.urls import path, include
from rest_framework import routers
from .views import UserViewSet, userProfileView, UsuarioGymViewSet, UsuarioGymDayViewSet, Home, MembresiaViewSet, MembresiaAsignadaViewSet, PagoMembresiaViewSet, ActivitiesView, ExportReportView, RegisterViewSet, DashboardStatsView, TipoEventoViewSet, EventoCalendarioViewSet, PublicCalendarioView, NotificationViewSet, CookieTokenObtainPairView, CookieTokenRefreshView, LogoutView

#api versioning
router = routers.DefaultRouter()
router.register(r'UserGym', UsuarioGymViewSet, basename='UserGym')
router.register(r'User', UserViewSet, basename='User')
router.register(r'UserGymDay', UsuarioGymDayViewSet, basename='UserGymDay')
router.register(r'MemberShips', MembresiaViewSet, basename='MemberShips')
router.register(r'MemberShipsAsignada', MembresiaAsignadaViewSet, basename='MemberShipsAsignada')
router.register(r'TiposEvento', TipoEventoViewSet, basename='TiposEvento')
router.register(r'CalendarioEventos', EventoCalendarioViewSet, basename='CalendarioEventos')
router.register(r'Notificaciones', NotificationViewSet, basename='Notificaciones')

urlpatterns = [
    path('gym/api/v1/', include(router.urls)),      
    
    path('gym/api/v1/register/', RegisterViewSet.as_view(), name='register'),
    path('gym/api/v1/me/', userProfileView.as_view(), name='user-profile'),
    path('gym/api/v1/list/', userProfileView.as_view(), name='user-list'),
    path('gym/api/v1/home/', Home.as_view(), name='home'),
    path('gym/api/v1/dashboard-stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('gym/api/v1/MemberShipsAsignada/<int:pk>/pagos/',
         PagoMembresiaViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='pagos-list'),
    path('gym/api/v1/activities/', ActivitiesView.as_view(), name='activities'),
    path('gym/api/v1/export-report/', ExportReportView.as_view(), name='export-report'),
    
    # SimpleJWT endpoints (cookie-based: login/refresh/logout)
    path('gym/api/v1/token/', CookieTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('gym/api/v1/token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('gym/api/v1/auth/logout/', LogoutView.as_view(), name='auth_logout'),
    
    # Endpoint público de calendario (NO bajo /gym/api/v1)
    path('api/calendario/publico/<int:gimnasio_id>/', PublicCalendarioView.as_view(), name='calendario-publico'),
]