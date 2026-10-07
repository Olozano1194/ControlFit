"""OperationLog model for audit trail of membership business operations."""

from django.db import models
from django.conf import settings
from .gym_model import Gimnasio
from .membership_model import MembresiaAsignada


class OperationLog(models.Model):
    """Append-only audit log for membership operations."""

    class OperationType(models.TextChoices):
        SUSPENDER = 'suspender'
        CAMBIAR_PLAN = 'cambiar_plan'
        DEVOLUCION = 'devolucion'
        RENOVAR = 'renovar'

    gimnasio = models.ForeignKey(
        Gimnasio,
        on_delete=models.CASCADE,
        related_name='operation_logs',
        help_text='Gym owning this log entry (tenant scope)'
    )
    membresia_asignada = models.ForeignKey(
        MembresiaAsignada,
        on_delete=models.CASCADE,
        related_name='operation_logs',
        help_text='Original assignment (for renovar, this is the original, not the new one)'
    )
    operation_type = models.CharField(
        max_length=20,
        choices=OperationType.choices,
        help_text='Type of operation performed'
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='operation_logs',
        help_text='User who performed the operation (nullable for system actors)'
    )
    reason = models.TextField(help_text='Verbatim reason provided for the operation')
    details = models.JSONField(default=dict, help_text='Schema per operation_type (REQ-4)')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'operation_log'
        ordering = ['-created_at', '-id']
        indexes = [
            models.Index(fields=['gimnasio', 'created_at'], name='oplog_gym_created_idx'),
            models.Index(fields=['membresia_asignada', 'created_at'], name='oplog_assignment_created_idx'),
        ]
        verbose_name = 'OperationLog'
        verbose_name_plural = 'OperationLogs'

    def __str__(self):
        return f'{self.operation_type} #{self.pk} {self.created_at:%Y-%m-%d}'