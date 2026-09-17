from django.db import models
from .membership_model import MembresiaAsignada



class PagoMembresia(models.Model):
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('nequi', 'Nequi'),
    ]

    membresia_asignada = models.ForeignKey(
        MembresiaAsignada,
        on_delete=models.CASCADE,
        related_name='pagos'
    )
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago = models.DateTimeField(auto_now_add=True)
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES)
    nota = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'Pago Membresia'
        verbose_name_plural = 'Pagos Membresia'
        db_table = 'pago_membresia'
        ordering = ['-fecha_pago']

    def __str__(self):
        return f"Pago {self.monto} - {self.metodo_pago} ({self.fecha_pago.strftime('%d/%m/%Y') if self.fecha_pago else '--'})"    

