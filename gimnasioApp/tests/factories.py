"""Factory functions for creating test objects.

These functions centralize object creation logic used across test modules.
All functions accept optional parameters with sensible defaults.

Models are imported lazily inside functions to avoid AppRegistryNotReady errors
when this module is imported outside of Django's test runner.
"""

from decimal import Decimal
from datetime import date, datetime, timezone as dt_timezone
from django.utils import timezone


def _get_models():
    """Lazy import of models to avoid AppRegistryNotReady."""
    from ..models import (
        Gimnasio, Usuario, UsuarioGym, Membresia, MembresiaAsignada,
        TipoEvento, EventoCalendario, DemoRequest
    )
    return (Gimnasio, Usuario, UsuarioGym, Membresia, MembresiaAsignada,
            TipoEvento, EventoCalendario, DemoRequest)


def create_gimnasio(name="Test Gym"):
    """Create a Gimnasio instance.

    Args:
        name: Name for the gym

    Returns:
        Gimnasio instance
    """
    Gimnasio, *_ = _get_models()
    return Gimnasio.objects.create(name=name)


def create_user(email, name, lastname, password, gimnasio, roles="recepcion"):
    """Create a Usuario instance.

    Args:
        email: User email
        name: User first name
        lastname: User last name
        password: User password
        gimnasio: Gimnasio instance to associate
        roles: User roles (default: "recepcion")

    Returns:
        Usuario instance
    """
    _, Usuario, *_ = _get_models()
    return Usuario.all_objects.create_user(
        email=email,
        name=name,
        lastname=lastname,
        password=password,
        gimnasio=gimnasio,
        roles=roles
    )


def create_admin_user(gimnasio):
    """Create an admin user.

    Args:
        gimnasio: Gimnasio instance to associate

    Returns:
        Usuario instance with admin role
    """
    return create_user(
        email="admin@example.com",
        name="Admin",
        lastname="User",
        password="password123",
        gimnasio=gimnasio,
        roles="admin"
    )


def create_miembro(name, lastname, gimnasio):
    """Create a UsuarioGym (member) instance.

    Args:
        name: Member first name
        lastname: Member last name
        gimnasio: Gimnasio instance to associate

    Returns:
        UsuarioGym instance
    """
    _, _, UsuarioGym, *_ = _get_models()
    return UsuarioGym.objects.create(
        name=name,
        lastname=lastname,
        gimnasio=gimnasio
    )


def create_membresia(gimnasio, name="Plan Test", price=50000, duration=30, max_multiplier=12):
    """Create a Membresia instance.

    Args:
        gimnasio: Gimnasio instance to associate
        name: Membership name
        price: Membership price
        duration: Duration in days
        max_multiplier: Maximum multiplier allowed

    Returns:
        Membresia instance
    """
    _, _, _, Membresia, *_ = _get_models()
    return Membresia.objects.create(
        name=name,
        price=Decimal(str(price)),
        duration=duration,
        max_multiplier=max_multiplier,
        gimnasio=gimnasio
    )


def create_membresia_asignada(miembro, membresia, date_initial=None, multiplier=1, discount=0):
    """Create a MembresiaAsignada instance.

    Args:
        miembro: UsuarioGym instance (member)
        membresia: Membresia instance
        date_initial: Start date (defaults to today)
        multiplier: Multiplier for price/duration calculation
        discount: Discount percentage

    Returns:
        MembresiaAsignada instance
    """
    _, _, _, _, MembresiaAsignada, *_ = _get_models()
    if date_initial is None:
        date_initial = date.today()

    return MembresiaAsignada.objects.create(
        miembro=miembro,
        membresia=membresia,
        dateInitial=date_initial,
        multiplier=Decimal(str(multiplier)),
        discount_percent=Decimal(str(discount))
    )


def _utc_datetime(year, month, day, hour=0, minute=0):
    """Helper: naive datetime -> aware UTC for calendar tests."""
    return timezone.make_aware(datetime(year, month, day, hour, minute), dt_timezone.utc)


def create_tipo_evento(gimnasio, nombre="Clase", color="#FF0000"):
    """Create a TipoEvento instance.

    Args:
        gimnasio: Gimnasio instance to associate
        nombre: Event type name
        color: Hex color code

    Returns:
        TipoEvento instance
    """
    _, _, _, _, _, TipoEvento, _, _ = _get_models()
    return TipoEvento.objects.create(
        nombre=nombre,
        color=color,
        gimnasio=gimnasio
    )


def create_evento_calendario(
    gimnasio,
    titulo="Evento",
    fecha_inicio=None,
    fecha_fin=None,
    tipo=None,
    created_by=None,
    descripcion="",
    relacion_tipo="",
    relacion_id=None
):
    """Create an EventoCalendario instance.

    Args:
        gimnasio: Gimnasio instance to associate
        titulo: Event title
        fecha_inicio: Start datetime (defaults to tomorrow 10:00 UTC)
        fecha_fin: End datetime (defaults to start + 2 hours)
        tipo: TipoEvento instance (optional)
        created_by: Usuario instance (optional)
        descripcion: Event description
        relacion_tipo: Related type string
        relacion_id: Related ID integer

    Returns:
        EventoCalendario instance
    """
    _, _, _, _, _, _, EventoCalendario, _ = _get_models()
    if fecha_inicio is None:
        fecha_inicio = _utc_datetime(2026, 8, 15, 10, 0)
    if fecha_fin is None:
        fecha_fin = _utc_datetime(2026, 8, 15, 12, 0)

    return EventoCalendario.objects.create(
        titulo=titulo,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        tipo=tipo,
        created_by=created_by,
        gimnasio=gimnasio,
        descripcion=descripcion,
        relacion_tipo=relacion_tipo,
        relacion_id=relacion_id
    )


def create_demo_request(
    nombre="Test User",
    email="test@example.com",
    telefono="123456789",
    nombre_gimnasio="Test Gym",
    estado="pendiente",
    gym_creado=None
):
    """Create a DemoRequest instance.

    Args:
        nombre: Requester name
        email: Requester email
        telefono: Requester phone
        nombre_gimnasio: Desired gym name
        estado: Request state (pendiente, contactado, cancelada)
        gym_creado: Gimnasio instance if created from this demo

    Returns:
        DemoRequest instance
    """
    _, _, _, _, _, _, _, DemoRequest = _get_models()
    return DemoRequest.objects.create(
        nombre=nombre,
        email=email,
        telefono=telefono,
        nombre_gimnasio=nombre_gimnasio,
        estado=estado,
        gym_creado=gym_creado
    )