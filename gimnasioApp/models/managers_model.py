from django.db import models
from django.contrib.auth.models import BaseUserManager



# ============================================================
# ACTIVE MANAGER - Filters is_active=True by default
# ============================================================
class ActiveManager(models.Manager):
    """Manager that filters to only active records (is_active=True) by default."""
    
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)
    
    def get_by_natural_key(self, email):
        """Required for Django authentication backend to work with custom User model."""
        return self.get_queryset().get(email=email)


# MANAGER
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
