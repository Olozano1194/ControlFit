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
    Lanza ValidationError si email ya existe en OTRO gym activo.
    Idempotente: si demo ya tiene gym_creado, reactiva si estaba inactivo.
    Si email existe pero es usuario inactivo de este gym, reactiva todo.
    """
    from ..models import Gimnasio, Usuario, DemoRequest
    
    # Idempotencia: si ya tiene gym_creado
    if demo_request.gym_creado:
        gym = demo_request.gym_creado
        
        # Si el gym estaba soft-deleted, reactivarlo
        if not gym.is_active:
            gym.is_active = True
            gym.save(update_fields=['is_active'])
            
            # Reactivar admin user(s)
            Usuario.objects.filter(gimnasio=gym, roles='admin').update(is_active=True)
        
        admin_user = Usuario.objects.filter(gimnasio=gym, roles='admin').first()
        temp_password = generate_temp_password()
        return gym, admin_user, temp_password
    
    # 1. Verificar email existente
    existing_user = Usuario.objects.filter(email=demo_request.email).first()
    
    if existing_user:
        # Si el usuario existe pero está INACTIVO y no tiene gimnasio (o gym inactivo)
        # Permitimos reactivarlo creando/usando el gym de la demo
        if not existing_user.is_active:
            # Verificar si tiene gimnasio asignado
            if existing_user.gimnasio and not existing_user.gimnasio.is_active:
                # Reactivar gym del usuario
                gym = existing_user.gimnasio
                gym.is_active = True
                gym.save(update_fields=['is_active'])
            else:
                # Crear gym nuevo
                gym = Gimnasio.objects.create(
                    name=demo_request.nombre_gimnasio,
                    phone=demo_request.telefono[:20],
                    address='',
                )
            
            # Reactivar usuario
            temp_password = generate_temp_password()
            existing_user.is_active = True
            existing_user.gimnasio = gym
            existing_user.roles = 'admin'
            existing_user.name = 'Admin'
            existing_user.lastname = demo_request.nombre_gimnasio[:50]
            existing_user.set_password(temp_password)
            existing_user.must_change_password = True
            existing_user.save()
            
            # Link demo -> gym
            demo_request.gym_creado = gym
            demo_request.save(update_fields=['gym_creado'])
            
            return gym, existing_user, temp_password
        else:
            # Usuario ACTIVO en otro lado -> error
            raise ValidationError("Este email ya está registrado. Usá otro email o contactá a soporte.")
    
    # 2. Email nuevo -> crear gym + usuario normalmente
    gym = Gimnasio.objects.create(
        name=demo_request.nombre_gimnasio,
        phone=demo_request.telefono[:20],
        address='',
    )
    
    temp_password = generate_temp_password()
    
    admin_user = Usuario.objects.create(
        email=demo_request.email,
        name='Admin',
        lastname=demo_request.nombre_gimnasio[:50],
        roles='admin',
        gimnasio=gym,
        password=make_password(temp_password),
        must_change_password=True,
        is_active=True,
    )
    
    demo_request.gym_creado = gym
    demo_request.save(update_fields=['gym_creado'])
    
    return gym, admin_user, temp_password


@transaction.atomic
def revert_gym_from_demo(demo_request) -> None:
    """
    Soft-delete: gym.is_active=False, admin.is_active=False, demo.gym_creado=None.
    Idempotente: si ya no tiene gym_creado, no hace nada.
    """
    from ..models import Usuario
    
    if not demo_request.gym_creado:
        return  # Ya revertido, idempotente
    
    gym = demo_request.gym_creado
    
    # Soft-delete gym
    gym.is_active = False
    gym.save(update_fields=['is_active'])
    
    # Soft-delete admin user(s) of this gym
    Usuario.objects.filter(gimnasio=gym, roles='admin').update(is_active=False)
    
    # Unlink demo
    demo_request.gym_creado = None
    demo_request.save(update_fields=['gym_creado'])