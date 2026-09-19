# Design: tests-refactor

## Technical Approach

Refactor `gimnasioApp/tests.py` (2015 lines, 26 test classes, 91 tests) into a domain-based package structure. Extract duplicated helpers, centralize fixtures, and split tests into focused modules while maintaining backward compatibility and dual test runner support.

## Architecture Decisions

### Decision: Package Structure

**Choice**: Create `gimnasioApp/tests/` package with domain-based modules
**Alternatives considered**: Keep monolith, split by test type (unit/integration)
**Rationale**: Domain grouping improves findability (tests for payments in one file), reduces merge conflicts, and aligns with Django's app-based architecture.

### Decision: Helper Deduplication

**Choice**: Centralize `_make_uploaded_image()` and `_make_request()` in `tests/helpers.py`
**Alternatives considered**: Keep in each test class, use factory_boy
**Rationale**: Reduces duplication (2 instances each), makes helpers reusable, avoids external dependencies.

### Decision: Fixture Strategy

**Choice**: Factory functions in `tests/factories.py` + pytest fixtures in `tests/conftest.py`
**Alternatives considered**: Only setUp() methods, only pytest fixtures
**Rationale**: Factory functions work with Django TestCase; pytest fixtures enable session-scoped optimization for expensive setup.

### Decision: Backward Compatibility

**Choice**: Explicit re-exports in `tests/__init__.py`
**Alternatives considered**: Dynamic imports, importlib
**Rationale**: Explicit imports are clear, IDE-friendly, and ensure `from gimnasioApp.tests import X` continues working.

## Data Flow

```
tests/__init__.py (re-exports)
    ↓ imports from
tests/test_*.py (domain modules)
    ↓ import from
tests/factories.py (object creation)
tests/helpers.py (utilities)
    ↓ pytest discovers
tests/conftest.py (fixtures)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `gimnasioApp/tests/` | Create | Package directory |
| `gimnasioApp/tests/__init__.py` | Create | Re-exports all 26 test classes |
| `gimnasioApp/tests/helpers.py` | Create | Deduplicated helper functions |
| `gimnasioApp/tests/factories.py` | Create | Factory functions for test objects |
| `gimnasioApp/tests/conftest.py` | Create | Pytest fixtures with scopes |
| `gimnasioApp/tests/test_middleware.py` | Create | GimnasioMiddlewareTest |
| `gimnasioApp/tests/test_mixins.py` | Create | MultiTenantViewSetMixinTest |
| `gimnasioApp/tests/test_views.py` | Create | UserViewSetCreateTest |
| `gimnasioApp/tests/test_storage.py` | Create | SupabaseMediaStorageTest, UsuarioSerializerAvatarTest |
| `gimnasioApp/tests/test_integration_avatar.py` | Create | AvatarUploadIntegrationTest |
| `gimnasioApp/tests/test_payments.py` | Create | 4 payment test classes |
| `gimnasioApp/tests/test_home_dashboard.py` | Create | HomeDashboardPagosTest |
| `gimnasioApp/tests/test_membership_models.py` | Create | 3 model test classes |
| `gimnasioApp/tests/test_serializers.py` | Create | 3 serializer test classes |
| `gimnasioApp/tests/test_email.py` | Create | EmailServiceTest |
| `gimnasioApp/tests/test_jwt_token.py` | Create | TokenLifetimeSettingsTest |
| `gimnasioApp/tests/test_csrf_cookie.py` | Create | CSRFSettingTest, CSRFCookieHelperTest |
| `gimnasioApp/tests/test_csrf_validation.py` | Create | CSRFValidationTest |
| `gimnasioApp/tests/test_auth_csrf.py` | Create | AuthViewsCSRFCookieTest |
| `gimnasioApp/tests/test_token_verify.py` | Create | TokenVerifyEndpointTest, TokenVerifyIntegrationTest |
| `gimnasioApp/tests/test_csrf_enforcement.py` | Create | CSRFEnforcementIntegrationTest, FullAuthFlowIntegrationTest |
| `gimnasioApp/tests.py` | Delete | Original monolith |

## Interfaces / Contracts

### Helper Functions

```python
# tests/helpers.py
def make_uploaded_image(filename='test.jpg', fmt='JPEG', size=(10, 10), color='red'):
    """Generate a valid image file using Pillow.
    
    Args:
        filename: Output filename
        fmt: Image format (JPEG, PNG)
        size: Tuple (width, height)
        color: Fill color
        
    Returns:
        SimpleUploadedFile instance
    """

def make_request_with_gym(factory, method='get', path='/', user=None, gimnasio=None, data=None, format=None):
    """Create a request with user and gimnasio attached.
    
    Args:
        factory: APIRequestFactory or RequestFactory instance
        method: HTTP method (get, post, patch, put, delete)
        path: Request path
        user: User instance to attach
        gimnasio: Gimnasio instance to attach
        data: Request data
        format: Request format (json, multipart)
        
    Returns:
        Request instance with user and gimnasio attributes
    """
```

### Factory Functions

```python
# tests/factories.py
def create_gimnasio(name="Test Gym"):
    """Create a Gimnasio instance."""

def create_user(email, name, lastname, password, gimnasio, roles="recepcion"):
    """Create a Usuario instance."""

def create_admin_user(gimnasio):
    """Create an admin user."""

def create_miembro(name, lastname, gimnasio):
    """Create a UsuarioGym instance."""

def create_membresia(gimnasio, name="Plan Test", price=50000, duration=30, max_multiplier=12):
    """Create a Membresia instance."""

def create_membresia_asignada(miembro, membresia, date_initial=None, multiplier=1, discount=0):
    """Create a MembresiaAsignada instance."""
```

### Pytest Fixtures

```python
# tests/conftest.py
@pytest.fixture(scope="session")
def gimnasio():
    """Session-scoped Gimnasio (expensive, immutable)."""

@pytest.fixture
def admin_user(gimnasio):
    """Function-scoped admin user."""

@pytest.fixture
def miembro(gimnasio):
    """Function-scoped member."""

@pytest.fixture
def membresia(gimnasio):
    """Function-scoped membership."""

@pytest.fixture
def membresia_asignada(miembro, membresia):
    """Function-scoped assigned membership."""
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Each test class in isolation | Django TestCase with factory functions |
| Integration | Cross-module interactions | Pytest fixtures with session scope |
| E2E | Full middleware stack | Django test client with CSRF tokens |

## Migration Patterns

### Pattern: Converting setUp() to Factories

**Before**:
```python
class MembresiaAsignadaSaveTest(TestCase):
    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Test Gym")
        self.membresia = Membresia.objects.create(
            name="Limited", price=10000, duration=30,
            max_multiplier=4, gimnasio=self.gimnasio
        )
        self.miembro = UsuarioGym.objects.create(
            name="Test", lastname="Member", gimnasio=self.gimnasio
        )
```

**After**:
```python
from .factories import create_gimnasio, create_membresia, create_miembro

class MembresiaAsignadaSaveTest(TestCase):
    def setUp(self):
        self.gimnasio = create_gimnasio()
        self.membresia = create_membresia(self.gimnasio, name="Limited", max_multiplier=4)
        self.miembro = create_miembro("Test", "Member", self.gimnasio)
```

### Pattern: Extracting Helpers

**Before**:
```python
class UsuarioSerializerAvatarTest(TestCase):
    def _make_uploaded_image(self, filename='test.jpg', fmt='JPEG'):
        from PIL import Image
        import io
        img = Image.new('RGB', (10, 10), color='red')
        buffer = io.BytesIO()
        img.save(buffer, format=fmt)
        return SimpleUploadedFile(filename, buffer.getvalue(), ...)
```

**After**:
```python
from .helpers import make_uploaded_image

class UsuarioSerializerAvatarTest(TestCase):
    # _make_uploaded_image removed, use make_uploaded_image() directly
```

## Test Discovery Configuration

### Django Test Runner

Django discovers `TestCase` subclasses in any module under `gimnasioApp/tests/`. The `__init__.py` with explicit imports ensures backward compatibility.

**Command**: `python manage.py test gimnasioApp`

### Pytest

Pytest auto-discovers `test_*.py` files and `conftest.py` in the package. No additional configuration needed.

**Command**: `pytest gimnasioApp/tests/`

**Verification**: `pytest --collect-only gimnasioApp/tests/` should show 91 items.

## Verification Checklist per Phase

### Phase 1: Foundation
```bash
# Create directory structure
mkdir -p gimnasioApp/tests

# Verify helpers work
python -c "from gimnasioApp.tests.helpers import make_uploaded_image; print('OK')"

# Verify factories work
python -c "from gimnasioApp.tests.factories import create_gimnasio; print('OK')"
```

### Phase 2: Extract Independent Modules
```bash
# After each module extraction
python manage.py test gimnasioApp.tests.test_jwt_token
pytest gimnasioApp/tests/test_jwt_token.py

# Verify count
python manage.py test gimnasioApp.tests.test_jwt_token --verbosity=2
```

### Phase 3: Extract Domain Modules
```bash
# After each module extraction
python manage.py test gimnasioApp.tests.test_payments
pytest gimnasioApp/tests/test_payments.py

# Verify no duplicate helpers
grep -r "_make_uploaded_image\|_make_request" gimnasioApp/tests/ | grep -v helpers.py
```

### Phase 4: Final Verification
```bash
# Full test suite
python manage.py test gimnasioApp
pytest gimnasioApp/tests/

# Backward compatibility
python -c "from gimnasioApp.tests import GimnasioMiddlewareTest; print('OK')"

# Line count verification
wc -l gimnasioApp/tests/test_*.py | sort -n
```

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Open Questions

- [ ] Should we add pytest-django configuration to `pyproject.toml` for explicit testpaths?
- [ ] Should `conftest.py` fixtures be function-scoped by default to prevent test pollution?
- [ ] Should we add type hints to factory functions for better IDE support?

## Next Step

Ready for implementation (sdd-apply).
