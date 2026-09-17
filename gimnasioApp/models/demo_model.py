from django.db import models
from .gym_model import Gimnasio



# ============================================================
# SOLICITUD DE DEMO
# ============================================================
class DemoRequest(models.Model):
    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('contactado', 'Contactado'),
        ('cancelada', 'Cancelada'),
    )
    nombre = models.CharField(max_length=150)
    email = models.EmailField()
    telefono = models.CharField(max_length=20)
    nombre_gimnasio = models.CharField(max_length=150)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    # FK al gimnasio creado desde esta demo (nullable, SET_NULL al borrar gimnasio)
    gym_creado = models.ForeignKey(
        Gimnasio,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='demo_origen'
    )

    class Meta:
        db_table = 'demo_request'
        verbose_name = 'Solicitud de Demo'
        verbose_name_plural = 'Solicitudes de Demo'
        ordering = ['-fecha_solicitud']

    def __str__(self):
        return f"{self.nombre_gimnasio} - {self.nombre}"