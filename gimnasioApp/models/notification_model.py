from django.db import models
from .gym_model import Gimnasio


# ============================================================
# NOTIFICACIONES — MODELO PERSISTENTE (Nivel 1)
# ============================================================

class Notification(models.Model):
    """Notificación persistente multi-tenant para el staff del gimnasio.

    Se genera de forma perezosa e idempotente desde la lista del API
    (vencimientos de membresías y eventos del día). La unicidad por
    (gimnasio, relacion_tipo, relacion_id, tipo) garantiza que un mismo
    origen no genere duplicados.
    """
    TIPO_CHOICES = [
        ('por_vencer', 'Por vencer'),
        ('vencida', 'Vencida'),
        ('evento', 'Evento'),
    ]
    gimnasio = models.ForeignKey(
        Gimnasio,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=False,
        blank=False
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    fecha = models.DateField()
    relacion_tipo = models.CharField(max_length=50, null=True, blank=True, default='')
    relacion_id = models.IntegerField(null=True, blank=True)
    link = models.TextField()
    whatsapp_link = models.TextField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        db_table = 'notification'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['gimnasio', 'relacion_tipo', 'relacion_id', 'tipo'],
                name='uq_notification_idempotency'
            )
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.titulo}"
