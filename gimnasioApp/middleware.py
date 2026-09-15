class GimnasioMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Superadmin no tiene gimnasio asignado - request.gimnasio queda en None
            # Los viewsets/mixins verificarán el rol para bypassear el filtro multi-tenant
            request.gimnasio = getattr(request.user, 'gimnasio', None)
        else:
            request.gimnasio = None
            # Intentar autenticar vía JWT para APIs que usan Bearer token
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
                try:
                    from rest_framework_simplejwt.tokens import AccessToken
                    from django.contrib.auth import get_user_model
                    access_token = AccessToken(token)
                    user_id = access_token.get('user_id')
                    if user_id:
                        User = get_user_model()
                        user = User.objects.get(id=user_id)
                        request.gimnasio = getattr(user, 'gimnasio', None)
                except Exception:
                    pass
        return self.get_response(request)


class CSRFValidationMiddleware:
    """Custom CSRF validation middleware for API endpoints.
    
    Validates X-CSRF-Token header against csrftoken cookie for mutating methods.
    In log-only mode (CSRF_ENFORCE=False): logs violations but allows request.
    In enforce mode (CSRF_ENFORCE=True): returns 403 for missing/mismatched tokens.
    
    GET requests always bypass validation. Only applies to /gym/api/v1/ paths.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only validate API paths
        if not request.path.startswith('/gym/api/v1/'):
            return self.get_response(request)

        # Only validate mutating methods
        if request.method not in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return self.get_response(request)

        # Skip validation for login, refresh, logout, verify, register endpoints
        # These are handled by their respective views
        skip_paths = (
            '/gym/api/v1/token/',
            '/gym/api/v1/token/refresh/',
            '/gym/api/v1/token/verify/',
            '/gym/api/v1/auth/logout/',
            '/gym/api/v1/register/',
        )
        if any(request.path.startswith(p) for p in skip_paths):
            return self.get_response(request)

        # Import here to avoid circular imports
        from gimnasioApp.views import validate_csrf
        from django.conf import settings
        from django.http import JsonResponse

        if not validate_csrf(request):
            # In enforce mode, validate_csrf returns False
            # We return 403 Forbidden
            if getattr(settings, 'CSRF_ENFORCE', False):
                return JsonResponse(
                    {'detail': 'CSRF validation failed. Missing or invalid X-CSRF-Token header.'},
                    status=403
                )
            # In log-only mode, validate_csrf logs and returns True, so we don't reach here

        return self.get_response(request)