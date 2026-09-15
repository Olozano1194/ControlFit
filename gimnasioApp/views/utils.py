import logging
from django.conf import settings
from django.http import request  # type only
from rest_framework.pagination import PageNumberPagination
from ..auth_cookie import get_csrf_token  # for validate_csrf

# Logger will be imported from parent package at runtime to support test patching
# See gimnasioApp.views.__init__ for the shared logger instance


# ============================================================
# CSRF VALIDATION
# ============================================================

def validate_csrf(request):
    """Validate CSRF token from X-CSRF-Token header against csrftoken cookie.
    
    In log-only mode (CSRF_ENFORCE=False): logs violations but allows request.
    In enforce mode (CSRF_ENFORCE=True): returns False for missing/mismatched tokens.
    
    GET requests always bypass validation.
    Mutating methods (POST, PUT, PATCH, DELETE) require validation.
    
    Returns:
        bool: True if validation passes (or is bypassed), False if validation fails in enforce mode.
    """
    # Import logger from parent package at runtime to support test patching
    from gimnasioApp.views import logger
    
    # GET requests bypass CSRF validation
    if request.method == 'GET':
        return True
    
    # Only validate mutating methods
    if request.method not in ('POST', 'PUT', 'PATCH', 'DELETE'):
        return True
    
    csrf_header = request.META.get('HTTP_X_CSRF_TOKEN')
    csrf_cookie = get_csrf_token(request)
    
    # Check if tokens match
    is_valid = csrf_header is not None and csrf_cookie is not None and csrf_header == csrf_cookie
    
    if not is_valid:
        logger.warning(
            'CSRF validation failed: method=%s path=%s header_present=%s cookie_present=%s',
            request.method,
            request.path,
            csrf_header is not None,
            csrf_cookie is not None
        )
        
        # In enforce mode, reject the request
        if getattr(settings, 'CSRF_ENFORCE', False):
            return False
    
    return True


# ============================================================
# PLATFORM PAGINATION
# ============================================================

class PlatformPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'