"""Onboarding service: provision and revert gym from demo requests."""

from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password
import secrets


def generate_temp_password(length: int = 12) -> str:
    """Genera password temporal URL-safe, alta entropía."""
    return secrets.token_urlsafe(length)[:length]


@transaction.atomic
def provision_gym_from_demo(demo_request) -> tuple:
    """
    Crea Gimnasio + Usuario(admin) + link demo.
    Retorna (gym, admin_user, temp_password).
    Lanza ValidationError si email ya existe.
    Idempotente: si demo ya tiene gym_creado, retorna el existente.
    """
    from ..models import Gimnasio, Usuario, DemoRequest
    
    # Idempotencia: si ya tiene gym_creado, retornar el existente
    if demo_request.gym_creado:
        gym = demo_request.gym_creado
        admin_user = Usuario.objects.filter(gimnasio=gym, roles='admin').first()
        # No tenemos el password original, generar uno nuevo (no usado en idempotencia)
        temp_password = generate_temp_password()
        return gym, admin_user, temp_password
    
    # 1. Validar email único
    if Usuario.objects.filter(email=demo_request.email).exists():
        raise ValidationError("Este email ya está registrado. Usá otro email o contactá a soporte.")
    
    # 2. Crear Gimnasio
    gym = Gimnasio.objects.create(
        name=demo_request.nombre_gimnasio,
        phone=demo_request.telefono[:20],  # truncar a 20
        address='',  # vacío por ahora
    )
    
    # 3. Password temporal
    temp_password = generate_temp_password()
    
    # 4. Crear Usuario admin
    admin_user = Usuario.objects.create(
        email=demo_request.email,
        name='Admin',
        lastname=demo_request.nombre_gimnasio[:50],  # truncar a 50
        roles='admin',
        gimnasio=gym,
        password=make_password(temp_password),
        must_change_password=True,
        is_active=True,
    )
    
    # 5. Link demo -> gym
    demo_request.gym_creado = gym
    demo_request.save(update_fields=['gym_creado'])
    
    return gym, admin_user, temp_password


@transaction.atomic
def revert_gym_from_demo(demo_request) -> None:
    """
    Soft-delete: gym.is_active=False, admin.is_active=False, demo.gym_creado=None.
    """
    from ..models import Usuario
    
    if demo_request.gym_creado:
        gym = demo_request.gym_creado
        # Soft-delete gym
        gym.is_active = False
        gym.save(update_fields=['is_active'])
        
        # Soft-delete admin user(s) of this gym
        Usuario.objects.filter(gimnasio=gym, roles='admin').update(is_active=False)
        
        # Unlink demo
        demo_request.gym_creado = None
        demo_request.save(update_fields=['gym_creado'])