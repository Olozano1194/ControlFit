"""Shared refresh-token cookie helpers (single source of truth for cookie attributes).

The cookie attributes are derived from ``settings.DEBUG`` at call time so the
environment is always reflected correctly:
- Development (DEBUG=True):  SameSite=Lax, no Secure flag (local HTTP).
- Production (DEBUG=False):  SameSite=None + Secure (cross-site Vercel -> Render).
"""

from django.conf import settings

REFRESH_COOKIE_KEY = 'refresh_token'
REFRESH_COOKIE_MAX_AGE = 604800  # 7 days
# RFC 6265 §5.4 path-match: el browser solo envía la cookie si este Path es
# prefijo de la URL pedida. Debe cubrir /token/refresh/ Y /auth/logout/ para
# que el logout pueda leerla y blacklistear el refresh server-side.
REFRESH_COOKIE_PATH = '/gym/api/v1/'


def set_refresh_cookie(response, refresh_token):
    """Set the refresh token as an HttpOnly cookie on the given response."""
    response.set_cookie(
        key=REFRESH_COOKIE_KEY,
        value=str(refresh_token),
        max_age=REFRESH_COOKIE_MAX_AGE,
        httponly=True,
        secure=not settings.DEBUG,
        samesite='None' if not settings.DEBUG else 'Lax',
        path=REFRESH_COOKIE_PATH,
    )


def clear_refresh_cookie(response):
    """Clear the refresh token cookie, mirroring the attributes used when setting it."""
    response.delete_cookie(
        key=REFRESH_COOKIE_KEY,
        path=REFRESH_COOKIE_PATH,
        samesite='None' if not settings.DEBUG else 'Lax',
    )