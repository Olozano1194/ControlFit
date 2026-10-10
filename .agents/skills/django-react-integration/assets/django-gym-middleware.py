# gimnasioApp/middleware.py

from django.utils.deprecation import MiddlewareMixin
from django.http import Http404
from .models.gym_model import Gimnasio


class GymMiddleware(MiddlewareMixin):
    """
    Multi-tenant gym resolution middleware.
    
    Flow:
    1. Superadmin (is_superuser) → request.gimnasio = None (access all)
    2. Authenticated user with gimnasio_id → request.gimnasio = user.gimnasio
    3. X-Gym-ID header provided → resolve Gimnasio (for API clients)
    4. None of above → request.gimnasio = None (will 403 in views)
    
    Views should use `request.gimnasio` to scope queries:
        Membership.objects.filter(miembro__gimnasio=request.gimnasio)
    """
    
    GYM_HEADER = 'HTTP_X_GYM_ID'  # Django normalizes X-Gym-ID
    
    def process_request(self, request):
        # Initialize
        request.gimnasio = None
        
        # Superadmin bypasses gym scoping
        if hasattr(request, 'user') and request.user.is_authenticated and request.user.is_superuser:
            return None
        
        # Try user's gym (from JWT auth)
        if hasattr(request, 'user') and request.user.is_authenticated:
            gym = getattr(request.user, 'gimnasio', None)
            if gym:
                request.gimnasio = gym
                return None
        
        # Try X-Gym-ID header (for API clients, mobile, etc.)
        gym_id = request.META.get(self.GYM_HEADER)
        if gym_id:
            try:
                request.gimnasio = Gimnasio.objects.get(id=gym_id, is_active=True)
            except (Gimnasio.DoesNotExist, ValueError):
                pass  # Will result in 403 in views that require gym
        
        return None


class RequireGymMiddleware(MiddlewareMixin):
    """
    Middleware to enforce gym context on specific paths.
    Use on views that MUST have a gym (not superadmin).
    """
    
    EXEMPT_PATHS = [
        '/api/auth/',
        '/admin/',
        '/static/',
        '/media/',
        '/health/',
    ]
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        # Skip exempt paths
        path = request.path_info
        if any(path.startswith(p) for p in self.EXEMPT_PATHS):
            return None
        
        # Superadmin exempt
        if request.user.is_authenticated and request.user.is_superuser:
            return None
        
        # Require gym context
        if not getattr(request, 'gimnasio', None):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(
                'Contexto de gimnasio requerido. '
                'Incluya header X-Gym-ID o inicie sesión como usuario de gimnasio.'
            )
        
        return None