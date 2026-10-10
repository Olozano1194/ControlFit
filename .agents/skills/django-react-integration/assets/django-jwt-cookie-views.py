# gimnasioApp/auth_cookie.py

from django.conf import settings
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer


# ============================================
# CUSTOM SERIALIZERS (add user data to response)
# ============================================

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Add user info to login response."""
    
    def validate(self, attrs):
        data = super().validate(attrs)
        # Add user data to response body (not in cookie)
        data['user'] = {
            'id': str(self.user.id),
            'email': self.user.email,
            'name': self.user.get_full_name(),
            'gym_id': str(self.user.gimnasio_id) if self.user.gimnasio_id else None,
            'is_superuser': self.user.is_superuser,
        }
        return data


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    """Rotate refresh token, return new access in body + cookie."""
    pass


# ============================================
# COOKIE HELPER FUNCTIONS
# ============================================

def set_jwt_cookies(response: Response, access: str, refresh: str = None) -> Response:
    """Set HttpOnly JWT cookies on response."""
    cookie_settings = {
        'secure': settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
        'httponly': settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
        'samesite': settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
        'path': settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
    }
    if settings.SIMPLE_JWT['AUTH_COOKIE_DOMAIN']:
        cookie_settings['domain'] = settings.SIMPLE_JWT['AUTH_COOKIE_DOMAIN']
    
    response.set_cookie(
        settings.SIMPLE_JWT['AUTH_COOKIE'],
        access,
        max_age=int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()),
        **cookie_settings
    )
    
    if refresh:
        response.set_cookie(
            settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
            refresh,
            max_age=int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
            **cookie_settings
        )
    
    return response


def clear_jwt_cookies(response: Response) -> Response:
    """Clear JWT cookies on logout."""
    cookie_names = [
        settings.SIMPLE_JWT['AUTH_COOKIE'],
        settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
    ]
    for name in cookie_names:
        response.delete_cookie(
            name,
            path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
            domain=settings.SIMPLE_JWT['AUTH_COOKIE_DOMAIN'],
            samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
        )
    return response


def get_csrf_token(request) -> str:
    """Get CSRF token for frontend."""
    return get_token(request)


# ============================================
# CUSTOM VIEWS
# ============================================

class CookieTokenObtainPairView(TokenObtainPairView):
    """
    POST /api/auth/login/
    Body: { "email": "...", "password": "..." }
    Response: { "user": {...} } + sets HttpOnly cookies
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]
    throttle_scope = 'login'
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        response = Response(serializer.validated_data, status=status.HTTP_200_OK)
        return set_jwt_cookies(
            response,
            serializer.validated_data['access'],
            serializer.validated_data['refresh']
        )


class CookieTokenRefreshView(TokenRefreshView):
    """
    POST /api/auth/refresh/
    Reads refresh from HttpOnly cookie, returns new access in body + cookie
    Rotates refresh token (blacklists old, issues new)
    """
    serializer_class = CustomTokenRefreshSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        # Get refresh token from cookie
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
        if not refresh_token:
            return Response(
                {'detail': 'Refresh token no encontrado en cookies'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Add to request data for serializer
        request.data['refresh'] = refresh_token
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        response = Response(serializer.validated_data, status=status.HTTP_200_OK)
        return set_jwt_cookies(
            response,
            serializer.validated_data['access'],
            serializer.validated_data.get('refresh')  # rotated refresh
        )


class CookieTokenLogoutView(APIView):
    """
    POST /api/auth/logout/
    Clears cookies, blacklists refresh token
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Blacklist refresh token if provided
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except (TokenError, InvalidToken):
                pass  # token already invalid/expired
        
        response = Response({'detail': 'Sesión cerrada correctamente'}, status=status.HTTP_200_OK)
        return clear_jwt_cookies(response)


class CSRFTokenView(APIView):
    """
    GET /api/auth/csrf/
    Returns CSRF token for frontend to use in mutations
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({'csrfToken': get_csrf_token(request)})


class MeView(APIView):
    """
    GET /api/auth/me/
    Returns current user info (validates access token)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        return Response({
            'id': str(user.id),
            'email': user.email,
            'name': user.get_full_name(),
            'gym_id': str(user.gimnasio_id) if user.gimnasio_id else None,
            'is_superuser': user.is_superuser,
        })


# ============================================
# CUSTOM AUTHENTICATION CLASS
# ============================================

class JWTCookieAuthentication:
    """
    DRF authentication that reads JWT from HttpOnly cookie.
    Falls back to Authorization header for API clients.
    """
    www_authenticate_realm = 'api'
    
    def authenticate(self, request):
        # Try cookie first
        access_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE'])
        
        # Fallback to Authorization header
        if not access_token:
            header = request.META.get('HTTP_AUTHORIZATION')
            if header and header.startswith('Bearer '):
                access_token = header.split(' ')[1]
        
        if not access_token:
            return None
        
        # Validate token
        from rest_framework_simplejwt.authentication import JWTAuthentication
        jwt_auth = JWTAuthentication()
        validated_token = jwt_auth.get_validated_token(access_token)
        user = jwt_auth.get_user(validated_token)
        
        return (user, validated_token)
    
    def authenticate_header(self, request):
        return f'Bearer realm="{self.www_authenticate_realm}"'