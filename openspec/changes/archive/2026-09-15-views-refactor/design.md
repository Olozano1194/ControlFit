# Design: Refactor views.py → Package views/

## Technical Approach

Split the 1,267-line monolithic `gimnasioApp/views.py` (22 classes + 2 utilities) into a Python package `gimnasioApp/views/` with 10 domain modules. The `__init__.py` re-exports all public symbols for full backward compatibility — no changes to `urls.py`, `middleware.py`, or test import paths.

## Architecture Decisions

### Decision: Import Strategy — No Circular Dependencies

**Choice**: Module-level absolute imports from `gimnasioApp.*` in each domain module. No lazy imports needed.

**Rationale**: Analysis of the dependency graph reveals zero circular dependency risk:

| Importer | Imports from | Cycle risk |
|----------|-------------|------------|
| `views/*.py` | `serializers.py` | **None** — serializers import only from `models.py`, never from views |
| `views/*.py` | `models.py` | **None** — models are leaf nodes |
| `views/*.py` | `services/*` | **None** — services import from `models.py` only |
| `views/*.py` | `mixins.py` | **None** — mixins have zero internal imports |
| `views/*.py` | `auth_cookie.py` | **None** — imports only `django.conf.settings` |
| `views/*.py` | `permissions.py` | **None** — imports only `rest_framework.permissions` |
| `middleware.py` → `views.utils` | Already lazy (`__call__` method) | **None** |
| `serializers.py` → `views` | Never imports from views | **None** |

Since the entire dependency graph is one-directional (views → everything else, nothing → views), every import can live at module level. This is the simplest and most Pythonic approach.

### Decision: Test Imports — Rely on __init__.py Re-export

**Choice**: Do NOT modify test import paths. Let `__init__.py` re-exports handle backward compatibility.

**Evidence**: `tests.py` line 20: `from .views import UserViewSet, UsuarioGymViewSet, MembresiaViewSet, Home, PagoMembresiaViewSet`. Lines 1417-1480: 7 occurrences of `from gimnasioApp.views import validate_csrf`. Lines 1515-1779: ~15 occurrences of `from gimnasioApp.views import CookieTokenObtainPairView` etc.

All 22 class names + `validate_csrf` will be in `__init__.py`'s namespace, so zero test changes needed.

### Decision: DemoRequestViewSet Placement

**Choice**: Place in `platform_views.py` (2 classes → 3 classes).

**Rationale**: The user's proposal lists 21 classes across 10 modules, but the codebase has 22. `DemoRequestViewSet` is an admin/sales domain view — it belongs with `PlatformStatsView` and `GimnasioPlatformViewSet`. Adding an 11th file for a single class is overhead.

### Decision: Module-Level Import Splitting

**Choice**: Each domain module gets exactly the imports it needs — no shared import block, no import-all.

**Rationale**: Clean dependency tracking per module. If `dashboard_views.py` imports `openpyxl`, that's visible only in `dashboard_views.py`. Makes future extraction or testing trivial.

### Decision: __init__.py Strategy

**Choice**: Explicit named imports from each submodule + `__all__` list.

**Rationale**: `from .auth_views import *` is fragile — it pulls everything unless `__all__` is set per module. Explicit imports make the public API visible at a glance and prevent accidental leak of internal helpers.

## Data Flow

```
Request → urls.py → (from .views import ClassName)
                          ↓
                     views/__init__.py (re-exports)
                          ↓
                     views/{domain}_views.py (actual implementation)
                          ↓
                     serializers.py → models.py
                     services/* → models.py
                     mixins.py (no deps)
                     permissions.py (no deps)
                     auth_cookie.py (django.conf only)
```

## Package Structure

```
gimnasioApp/views/
├── __init__.py              # Re-exports all 22 classes + validate_csrf
├── utils.py                 # validate_csrf, PlatformPagination
├── auth_views.py            # CookieTokenObtainPairView, CookieTokenRefreshView,
│                            # CookieTokenVerifyView, LogoutView, RegisterViewSet,
│                            # PasswordChangeView
├── member_views.py          # UserViewSet, UsuarioGymViewSet, UsuarioGymDayViewSet
├── membership_views.py      # MembresiaViewSet, MembresiaAsignadaViewSet
├── payment_views.py         # PagoMembresiaViewSet
├── dashboard_views.py       # DashboardStatsView, Home, ActivitiesView, ExportReportView
├── notification_views.py    # NotificationViewSet
├── calendar_views.py        # TipoEventoViewSet, EventoCalendarioViewSet, PublicCalendarioView
├── platform_views.py        # PlatformStatsView, GimnasioPlatformViewSet, DemoRequestViewSet
└── profile_views.py         # userProfileView
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `gimnasioApp/views/` | Create | Package directory |
| `gimnasioApp/views/__init__.py` | Create | Re-exports all 22 classes + validate_csrf |
| `gimnasioApp/views/utils.py` | Create | validate_csrf (lines 43-82), PlatformPagination (lines 89-93) |
| `gimnasioApp/views/auth_views.py` | Create | 6 auth classes (lines 147-351) |
| `gimnasioApp/views/member_views.py` | Create | 3 member classes (lines 100-405) |
| `gimnasioApp/views/membership_views.py` | Create | 2 membership classes (lines 593-616) |
| `gimnasioApp/views/payment_views.py` | Create | 1 payment class (lines 623-651) |
| `gimnasioApp/views/dashboard_views.py` | Create | 4 dashboard classes (lines 412-970) |
| `gimnasioApp/views/notification_views.py` | Create | 1 notification class (lines 658-702) |
| `gimnasioApp/views/calendar_views.py` | Create | 3 calendar classes (lines 977-1010) |
| `gimnasioApp/views/platform_views.py` | Create | 3 platform classes (lines 1026-1267) |
| `gimnasioApp/views/profile_views.py` | Create | 1 profile class (lines 354-375) |
| `gimnasioApp/views.py` | Delete | Replaced by package (after verification) |

## Import Map Per Module

### utils.py
```python
import logging
from django.conf import settings
from django.http import request  # type only
from rest_framework.pagination import PageNumberPagination
from .auth_cookie import get_csrf_token  # for validate_csrf
```

### auth_views.py
```python
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from .auth_cookie import set_refresh_cookie, clear_refresh_cookie, set_csrf_cookie, clear_csrf_cookie
from .serializers import UsuarioSerializer, PasswordChangeSerializer
from .models import Gimnasio
```

### member_views.py
```python
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from .serializers import UsuarioSerializer, UsuarioGymSerializer, UsuarioGymDaySerializer
from .models import Usuario, UsuarioGym, UsuarioGymDay
from .permissions import IsAdminUser, IsRecepcionUser, RequirePasswordChange
from .mixins import MultiTenantViewSetMixin
```

### membership_views.py
```python
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from .serializers import MembresiasSerializer, MembresiaAsignadaSerializer
from .models import Membresia, MembresiaAsignada
from .permissions import IsRecepcionUser, RequirePasswordChange
from .mixins import MultiTenantViewSetMixin
```

### payment_views.py
```python
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .serializers import PagoMembresiaSerializer
from .models import MembresiaAsignada, PagoMembresia
from .permissions import IsRecepcionUser, RequirePasswordChange
```

### dashboard_views.py
```python
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal
from datetime import datetime, date, timedelta
from .serializers import MembresiasSerializer
from .models import MembresiaAsignada, UsuarioGymDay, PagoMembresia
from .permissions import RequirePasswordChange
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
```

### notification_views.py
```python
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.utils import timezone
from .serializers import NotificationSerializer
from .models import Notification
from .permissions import IsRecepcionUser, RequirePasswordChange
from .mixins import MultiTenantViewSetMixin
from .services.notifications import NotificationManager
```

### calendar_views.py
```python
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from .serializers import TipoEventoSerializer, EventoCalendarioSerializer
from .models import TipoEvento, EventoCalendario, Gimnasio
from .permissions import IsAdminUser, IsRecepcionUser, RequirePasswordChange
from .mixins import MultiTenantViewSetMixin
```

### platform_views.py
```python
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q, Sum
from django.db import transaction
from datetime import date, timedelta
from decimal import Decimal
from .serializers import (
    DemoRequestSerializer, PlatformStatsSerializer,
    GimnasioPlatformSerializer, GimnasioPlatformDetailSerializer,
)
from .models import DemoRequest, Gimnasio, MembresiaAsignada, PagoMembresia, UsuarioGymDay, Usuario
from .permissions import IsSuperAdmin, RequirePasswordChange
from .utils import PlatformPagination
from .services.onboarding import provision_gym_from_demo, revert_gym_from_demo
from .services.email import send_welcome_email
import logging
```

### profile_views.py
```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import UsuarioSerializer
from .models import Usuario
from .permissions import RequirePasswordChange
```

## __init__.py Content

```python
"""gimnasioApp views package — re-exports all public classes for backward compatibility."""

from .utils import validate_csrf, PlatformPagination
from .auth_views import (
    CookieTokenObtainPairView,
    CookieTokenRefreshView,
    CookieTokenVerifyView,
    LogoutView,
    RegisterViewSet,
    PasswordChangeView,
)
from .member_views import UserViewSet, UsuarioGymViewSet, UsuarioGymDayViewSet
from .membership_views import MembresiaViewSet, MembresiaAsignadaViewSet
from .payment_views import PagoMembresiaViewSet
from .dashboard_views import DashboardStatsView, Home, ActivitiesView, ExportReportView
from .notification_views import NotificationViewSet
from .calendar_views import TipoEventoViewSet, EventoCalendarioViewSet, PublicCalendarioView
from .platform_views import PlatformStatsView, GimnasioPlatformViewSet, DemoRequestViewSet
from .profile_views import userProfileView

__all__ = [
    'validate_csrf',
    'PlatformPagination',
    'CookieTokenObtainPairView',
    'CookieTokenRefreshView',
    'CookieTokenVerifyView',
    'LogoutView',
    'RegisterViewSet',
    'PasswordChangeView',
    'UserViewSet',
    'UsuarioGymViewSet',
    'UsuarioGymDayViewSet',
    'MembresiaViewSet',
    'MembresiaAsignadaViewSet',
    'PagoMembresiaViewSet',
    'DashboardStatsView',
    'Home',
    'ActivitiesView',
    'ExportReportView',
    'NotificationViewSet',
    'TipoEventoViewSet',
    'EventoCalendarioViewSet',
    'PublicCalendarioView',
    'PlatformStatsView',
    'GimnasioPlatformViewSet',
    'DemoRequestViewSet',
    'userProfileView',
]
```

## Middleware Compatibility

`middleware.py` line 64: `from gimnasioApp.views import validate_csrf` — works unchanged because `__init__.py` re-exports `validate_csrf`. No code change needed.

## Migration Order (Incremental Verification)

| Step | Module | Verification |
|------|--------|-------------|
| 1 | `utils.py` | `python -c "from gimnasioApp.views.utils import validate_csrf"` |
| 2 | `auth_views.py` | `python -c "from gimnasioApp.views.auth_views import RegisterViewSet"` |
| 3 | `profile_views.py` | `python -c "from gimnasioApp.views.profile_views import userProfileView"` |
| 4 | `member_views.py` | `python -c "from gimnasioApp.views.member_views import UserViewSet"` |
| 5 | `membership_views.py` | `python -c "from gimnasioApp.views.membership_views import MembresiaViewSet"` |
| 6 | `payment_views.py` | `python -c "from gimnasioApp.views.payment_views import PagoMembresiaViewSet"` |
| 7 | `notification_views.py` | `python -c "from gimnasioApp.views.notification_views import NotificationViewSet"` |
| 8 | `calendar_views.py` | `python -c "from gimnasioApp.views.calendar_views import TipoEventoViewSet"` |
| 9 | `dashboard_views.py` | `python -c "from gimnasioApp.views.dashboard_views import Home"` |
| 10 | `platform_views.py` | `python -c "from gimnasioApp.views.platform_views import PlatformStatsView"` |
| 11 | `__init__.py` | `python -c "from gimnasioApp.views import UserViewSet"` |
| 12 | Delete `views.py` | `python manage.py test gimnasioApp --verbosity=1` |

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Import | All 22 classes importable from `gimnasioApp.views` | `python -c` per class |
| Import | `validate_csrf` importable from `gimnasioApp.views` | `python -c` |
| Unit | All 91 existing tests pass unchanged | `python manage.py test gimnasioApp` |
| Integration | `urls.py` resolves all routes | Django startup (test runner does this) |
| Regression | No API behavior changes | Existing test assertions |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Rollback Procedure

1. Delete `gimnasioApp/views/` directory
2. `git checkout gimnasioApp/views.py` (restore original file)
3. `python manage.py test gimnasioApp --verbosity=1` — confirm 91 tests pass
4. Total time: < 2 minutes

## Open Questions

- [ ] None — all dependencies analyzed, no unresolved decisions.
