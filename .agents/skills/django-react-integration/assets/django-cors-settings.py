# gimnasio/settings/base.py (relevant sections)

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ============================================
# CORS + CSRF + COOKIES
# ============================================

INSTALLED_APPS = [
    # ...
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt',
    'gimnasioApp',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # MUST be before CommonMiddleware
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # static files in prod
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Custom middleware (order matters)
    'gimnasioApp.middleware.GymMiddleware',  # sets request.gimnasio from X-Gym-ID
    'gimnasioApp.auth_cookie.JWTCookieMiddleware',  # reads JWT from cookies
]

# CORS - dev + prod
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',  # Vite dev
    'https://tudominio.com',  # production
]
CORS_ALLOW_CREDENTIALS = True  # REQUIRED for cookies
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-gym-id',  # custom header for multi-tenant
]

# CSRF
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:5173',
    'https://tudominio.com',
]
CSRF_COOKIE_SECURE = True  # HTTPS only in prod
CSRF_COOKIE_HTTPONLY = True  # JS cannot read
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = False  # use cookie, not session

# Session / JWT Cookies
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# ============================================
# SIMPLE JWT (cookie-based)
# ============================================

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    # Cookie settings
    'AUTH_COOKIE': 'access',
    'AUTH_COOKIE_REFRESH': 'refresh',
    'AUTH_COOKIE_DOMAIN': None,  # set in prod: '.tudominio.com'
    'AUTH_COOKIE_SECURE': True,
    'AUTH_COOKIE_HTTP_ONLY': True,
    'AUTH_COOKIE_PATH': '/',
    'AUTH_COOKIE_SAMESITE': 'Lax',
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': os.environ.get('JWT_SECRET_KEY'),
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# ============================================
# DRF
# ============================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'gimnasioApp.auth_cookie.JWTCookieAuthentication',  # reads from cookie
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/min',
        'user': '1000/min',
        'login': '10/min',
    },
    'EXCEPTION_HANDLER': 'gimnasioApp.utils.custom_exception_handler',
}

# ============================================
# STATIC / MEDIA (prod)
# ============================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'gimnasioReact' / 'dist',  # React build output
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ============================================
# WHITENOISE (prod static serving)
# ============================================

WHITENOISE_USE_FINDERS = True
WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_ALLOW_ALL_ORIGINS = True

# ============================================
# MULTI-TENANT GYM SETTINGS
# ============================================

GYM_HEADER_NAME = 'HTTP_X_GYM_ID'  # Django normalizes X-Gym-ID to HTTP_X_GYM_ID
DEFAULT_GYM_ID = None  # None = superadmin context