"""Pytest fixtures for gimnasioApp tests.

Provides session-scoped and function-scoped fixtures for test setup.
Session-scoped fixtures are used for expensive, immutable objects.
Function-scoped fixtures ensure test isolation.
"""

import pytest

from .factories import (
    create_gimnasio,
    create_admin_user,
    create_miembro,
    create_membresia,
    create_membresia_asignada,
)


@pytest.fixture(scope="session")
def gimnasio():
    """Session-scoped Gimnasio (expensive, immutable).

    Creates a single gym instance shared across all tests in the session.
    Use this for tests that don't modify the gimnasio.
    """
    return create_gimnasio()


@pytest.fixture
def admin_user(gimnasio):
    """Function-scoped admin user.

    Creates a fresh admin user for each test that needs one.
    """
    return create_admin_user(gimnasio)


@pytest.fixture
def miembro(gimnasio):
    """Function-scoped member.

    Creates a fresh member for each test.
    """
    return create_miembro("Test", "Member", gimnasio)


@pytest.fixture
def membresia(gimnasio):
    """Function-scoped membership.

    Creates a fresh membership for each test.
    """
    return create_membresia(gimnasio)


@pytest.fixture
def membresia_asignada(miembro, membresia):
    """Function-scoped assigned membership.

    Creates a fresh MembresiaAsignada for each test.
    """
    return create_membresia_asignada(miembro, membresia)