from django.db import models
from .gym_model import Gimnasio


# ============================================================
# MODELO USUARIO
# ============================================================
class UsuarioGym(models.Model):
    name = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    phone = models.CharField(max_length=10)
    # user = models.OneToOneField(User, on_delete=models.CASCADE)
    address = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # FK a Gimnasio para multi-tenant
    gimnasio = models.ForeignKey(
        Gimnasio,
        on_delete=models.CASCADE,
        related_name='miembros',
        null=False,
        blank=False
    )

    def __str__(self):
        return f"{self.name} {self.lastname}"
    
    class Meta:
        verbose_name = 'UsuarioGym'
        verbose_name_plural = 'UsuarioGyms'
        db_table = 'usuarioGym'
        ordering = ['-created_at']
    
class UsuarioGymDay(models.Model):
    name = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    phone = models.CharField(max_length=10)
    # user = models.OneToOneField(User, on_delete=models.CASCADE)
    dateInitial = models.DateField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # FK a Gimnasio para multi-tenant
    gimnasio = models.ForeignKey(
        Gimnasio,
        on_delete=models.CASCADE,
        related_name='miembros_diarios',
        null=False,
        blank=False
    )

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'UsuarioGymDay'
        verbose_name_plural = 'UsuarioGymDays'
        db_table = 'usuarioGymDay'
        ordering = ['-created_at']
