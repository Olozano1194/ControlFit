from django.db import models
from .managers_model import ActiveManager

# ============================================================
# MODELO GIMNASIO - Para multi-tenant
# ============================================================
class Gimnasio(models.Model):
    """Representa cada gimnasio/cliente en el sistema multi-tenant."""
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200, blank=True, default='')
    phone = models.CharField(max_length=20, blank=True, default='')
    is_active = models.BooleanField(default=True)
    country_code = models.CharField(max_length=5, default='57', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Managers: objects filters active; all_objects returns all
    objects = ActiveManager()
    all_objects = models.Manager()
    
    class Meta:
        db_table = 'gimnasio'
        verbose_name = 'Gimnasio'
        verbose_name_plural = 'Gimnasios'
        ordering = ['name']
    
    def __str__(self):
        return self.name

