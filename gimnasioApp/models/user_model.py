from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from .gym_model import Gimnasio
from .managers_model import ActiveManager, UserManager

# ============================================================
# MODELO USUARIO
# ============================================================
class UserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        """
        Crea un usuario.
        """
        if not email:
            raise ValueError('Los usuarios deben tener un correo electrónico')
        
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save()
        return user

class Usuario(AbstractBaseUser):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=45)
    lastname = models.CharField(max_length=50)
    #user = models.CharField(max_length=30, unique=True)
    avatar = models.ImageField(upload_to='fotos/', null=True, blank=True, default='')
    
    # FK a Gimnasio para multi-tenant
    # null/blank=True para permitir superadmin SIN gimnasio asignado
    gimnasio = models.ForeignKey(
        Gimnasio,
        on_delete=models.CASCADE,
        related_name='usuarios',
        null=True,
        blank=True
    )
        
    OPCIONES_ROL = [
        ('recepcion', 'Recepcionista'),
        ('admin', 'Administrador'),
        ('superadmin', 'Super Administrador'),
    ]
    roles = models.CharField(max_length=10, choices=OPCIONES_ROL, default='recepcion')
    #password = models.CharField(max_length=300)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Campo para forzar cambio de contraseña en primer login
    must_change_password = models.BooleanField(default=False)

    # Usamos ActiveManager como default (filtra is_active=True)
    # UserManager se mantiene disponible via all_objects para admin/creation
    objects = ActiveManager()
    all_objects = UserManager()

    # Se define el campo de autenticación sea el email
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'lastname']

    def full_name(self):
        return '{} {}'.format(self.name, self.lastname)

    def __str__(self):
        return self.full_name()
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        db_table = 'usuario'
        ordering = ['created_at']
