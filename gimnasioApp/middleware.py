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