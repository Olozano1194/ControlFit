from django.db import models
from .gym_model import Gimnasio
from .user_model import Usuario



# ============================================================
# CALENDARIO — TIPO DE EVENTO Y EVENTO DE CALENDARIO
# ============================================================

class TipoEvento(models.Model):
    """Tipo de evento del calendario (multi-tenant por gimnasio)."""
    nombre = models.CharField(max_length=100)
    color = models.CharField(max_length=7)  # e.g. #FF0000
    gimnasio = models.ForeignKey(
        Gimnasio,
        on_delete=models.CASCADE,
        related_name='tipos_evento',
        null=False,
        blank=False
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'TipoEvento'
        verbose_name_plural = 'TipoEventos'
        db_table = 'tipo_evento'
        ordering = ['nombre']


class EventoCalendario(models.Model):
    """Evento del calendario (multi-tenant por gimnasio)."""
    titulo = models.CharField(max_length=200)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    descripcion = models.TextField(blank=True, default='')
    tipo = models.ForeignKey(
        TipoEvento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='eventos'
    )
    relacion_tipo = models.CharField(max_length=50, null=True, blank=True, default='')
    relacion_id = models.IntegerField(null=True, blank=True)
    created_by = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='eventos_creados'
    )
    gimnasio = models.ForeignKey(
        Gimnasio,
        on_delete=models.CASCADE,
        related_name='eventos_calendario',
        null=False,
        blank=False
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = 'EventoCalendario'
        verbose_name_plural = 'EventoCalendarios'
        db_table = 'evento_calendario'
        ordering = ['fecha_inicio']

