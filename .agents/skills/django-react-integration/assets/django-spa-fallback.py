# gimnasio/urls.py

from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static


# SPA fallback view - serves React index.html for all non-API routes
spa_view = TemplateView.as_view(template_name='index.html')


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API routes (must come before SPA fallback)
    path('api/auth/', include('gimnasioApp.urls_auth')),  # login, refresh, logout, me, csrf
    path('api/', include('gimnasioApp.urls_api')),  # all other API endpoints
    
    # Health check (for load balancers)
    path('health/', include('gimnasioApp.urls_health')),
]


# ============================================
# SPA FALLBACK (catch-all for React Router)
# ============================================

# Only in production (Django serves React build)
# In dev, Vite handles routing via dev server
if not settings.DEBUG:
    urlpatterns += [
        # Serve React app for all non-API, non-admin, non-static, non-media routes
        re_path(r'^(?!api/|admin/|static/|media/|health/).*$', spa_view, name='spa-fallback'),
    ]
else:
    # Dev: still need a catch-all for direct URL access (refresh, bookmarks)
    # Vite proxy handles /api, but direct navigation to /dashboard needs this
    urlpatterns += [
        re_path(r'^(?!api/|admin/|static/|media/|health/).*$', spa_view, name='spa-fallback'),
    ]


# ============================================
# STATIC / MEDIA (dev only)
# ============================================

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)