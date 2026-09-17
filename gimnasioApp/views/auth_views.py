from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from ..auth_cookie import set_refresh_cookie, clear_refresh_cookie, set_csrf_cookie, clear_csrf_cookie
from ..serializers.profile_serializer import UsuarioSerializer
from ..serializers.auth_serializer import PasswordChangeSerializer
from ..models import Gimnasio


# ============================================================
# PUBLIC REGISTRATION
# ============================================================

class RegisterViewSet(APIView):
    """Public self-service registration endpoint.

    INTENTIONAL: This endpoint uses AllowAny permission to allow gym owners
    to create their account without prior authentication. This is by design.

    Threat Model:
    - Spam registrations: Mitigated by email uniqueness constraint and
      automatic gym creation (each registration creates a Gimnasio record).
      Rate limiting SHOULD be added in a future phase.
    - Abuse: Each registration creates a full gym + admin user. Consider
      CAPTCHA or email verification in future hardening.
    - Data exposure: Only returns user data for the created account.
      No cross-tenant data leakage possible.

    Protections in place:
    - Email uniqueness (database constraint + serializer validation)
    - Password hashing (set_password via AbstractBaseUser)
    - No sensitive data exposed in response
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        name = request.data.get('name')
        lastname = request.data.get('lastname')

        if not email or not password or not name or not lastname:
            return Response({
                'error': 'Todos los campos son requeridos',
                'required': ['email', 'password', 'name', 'lastname']
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verificar si el usuario ya existe
        if get_user_model().objects.filter(email=email).exists():
            return Response({'error': 'El correo ya está registrado'}, status=status.HTTP_400_BAD_REQUEST)

        # Crear gimnasio automáticamente
        email_prefix = email.split('@')[0].replace('.', ' ').title()
        gimnasio = Gimnasio.objects.create(name=f"Gimnasio {email_prefix}")

        # Crear usuario con gimnasio
        user = get_user_model()(
            email=email,
            name=name,
            lastname=lastname,
            roles='admin',  # Primer usuario es admin
            gimnasio=gimnasio
        )
        user.set_password(password)
        user.save()

        # Generar tokens JWT
        refresh = RefreshToken.for_user(user)

        response = Response({
            'message': 'Usuario creado exitosamente',
            'user': UsuarioSerializer(user, context={'request': request}).data,
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

        # Establecer refresh token como cookie HttpOnly (helper compartido)
        set_refresh_cookie(response, refresh)
        set_csrf_cookie(response, refresh)

        return response


# ============================================================
# AUTH JWT — LOGIN / REFRESH / LOGOUT (cookie-based)
# ============================================================

class CookieTokenObtainPairView(TokenObtainPairView):
    """Login: valida credenciales, setea el refresh como cookie HttpOnly y devuelve solo access."""
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            refresh = response.data.get('refresh')
            if refresh:
                set_refresh_cookie(response, refresh)
                set_csrf_cookie(response, refresh)  # Use refresh as CSRF token source
                del response.data['refresh']  # Nunca exponer el refresh en el body
        return response


class CookieTokenRefreshView(TokenRefreshView):
    """Refresh: lee el refresh de la COOKIE (no del body), rota y re-setea la cookie."""
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({'detail': 'No refresh token'}, status=status.HTTP_401_UNAUTHORIZED)

        # Inyectar el refresh desde la cookie directo al serializer (mismo flujo que TokenViewBase)
        serializer = self.get_serializer(data={'refresh': refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        response = Response(serializer.validated_data, status=status.HTTP_200_OK)

        new_refresh = response.data.get('refresh')
        if new_refresh:
            set_refresh_cookie(response, new_refresh)
            set_csrf_cookie(response, new_refresh)  # Set new CSRF cookie with rotated refresh
            del response.data['refresh']
        return response


class LogoutView(APIView):
    """Logout: blacklistea el refresh de la cookie y limpia la cookie (idempotente)."""
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except Exception:
                # Token inválido/expirado/ya blacklistado: seguimos y limpiamos igual
                pass
        response = Response({'detail': 'Logged out'})
        clear_refresh_cookie(response)
        clear_csrf_cookie(response)
        return response


# ============================================================
# TOKEN VERIFY ENDPOINT
# ============================================================

class CookieTokenVerifyView(APIView):
    """Verify: lee el access token del header Authorization, valida y devuelve {valid: true, exp: timestamp} o 401.

    Accepts both GET and POST for compatibility. GET is preferred (read-only, no CSRF needed).
    """
    permission_classes = [AllowAny]

    def get(self, request):
        return self._verify(request)

    def post(self, request):
        return self._verify(request)

    def _verify(self, request):
        # Extract token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return Response(
                {'detail': 'Authorization header missing or invalid'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        token_str = auth_header[7:]  # Remove 'Bearer ' prefix

        # Validate the access token
        try:
            access_token = AccessToken(token_str, verify=True)
        except (TokenError, InvalidToken):
            return Response(
                {'detail': 'Token is invalid or expired'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Return valid response with exp timestamp
        return Response({
            'valid': True,
            'exp': access_token.payload.get('exp')
        }, status=status.HTTP_200_OK)


# ============================================================
# PASSWORD CHANGE ENDPOINT
# ============================================================

class PasswordChangeView(APIView):
    """Cambio de contraseña para usuarios con must_change_password=True."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']

        # Verificar password actual
        if not user.check_password(old_password):
            return Response(
                {'old_password': 'La contraseña actual es incorrecta.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Actualizar password y resetear flag
        user.set_password(new_password)
        user.must_change_password = False
        user.save(update_fields=['password', 'must_change_password'])

        return Response({'detail': 'Contraseña actualizada correctamente. Inicia sesión de nuevo.'})