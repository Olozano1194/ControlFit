from django.db import models
from .gym_model import Gimnasio
from .member_model import UsuarioGym
from datetime import timedelta, date
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db.models import Sum




# ============================================================
# Membresias
# ============================================================
class Membresia(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.PositiveIntegerField(help_text="Duración en días (1-365)")
    max_multiplier = models.PositiveIntegerField(default=1, help_text="Máximo multiplicador permitido (1 = no multiplicable)")
    is_active = models.BooleanField(default=True)
    
    # FK a Gimnasio para multi-tenant
    gimnasio = models.ForeignKey(
        Gimnasio,
        on_delete=models.CASCADE,
        related_name='membresias',
        null=False,
        blank=False
    )

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Membresia'
        verbose_name_plural = 'Membresias'
        db_table = 'membresia'
        unique_together = ('gimnasio', 'name')

class MembresiaAsignada(models.Model):
    gimnasio = models.ForeignKey(Gimnasio, on_delete=models.CASCADE, related_name='membresias_asignadas', null=False, blank=False)
    miembro = models.ForeignKey(UsuarioGym, on_delete=models.CASCADE, related_name='miembro')
    membresia = models.ForeignKey(Membresia, on_delete=models.CASCADE)
    multiplier = models.DecimalField(default=1, max_digits=4, decimal_places=1, help_text="Multiplicador de duración/precio (1 = sin multiplicar)")
    discount_percent = models.DecimalField(default=0, max_digits=5, decimal_places=2, help_text="Descuento porcentual (0-100)")
    dateInitial = models.DateField()
    dateFinal = models.DateField(editable=False, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'MembresiaAsignada'
        verbose_name_plural = 'MembresiaAsignadas'
        db_table = 'membresiaAsignada'
        ordering = ['-dateInitial']
    
    def save(self, *args, **kwargs):
        if not self.gimnasio_id and self.miembro_id:
            self.gimnasio = self.miembro.gimnasio
        # Ensure dateInitial is a date object, not a string
        inicio = self.dateInitial
        if isinstance(inicio, str):
            try:
                partes = inicio.split('-')
                inicio = date(int(partes[0]), int(partes[1]), int(partes[2]))
            except (IndexError, ValueError):
                raise ValidationError("Formato de fecha inválido. Use YYYY-MM-DD.")
        if not self.pk:  # Only on creation
            if int(self.multiplier) > self.membresia.max_multiplier:
                if self.membresia.max_multiplier <= 1:
                    raise ValidationError("Esa membresía no se puede multiplicar")
                raise ValidationError(
                    f"Esa membresía solo permite hasta {self.membresia.max_multiplier} periodos"
                )
        # Always recalculate using stored multiplier and discount_percent
        mult = Decimal(str(self.multiplier))
        disc = Decimal(str(self.discount_percent or 0))
        dias_totales = int(self.membresia.duration * mult)
        self.dateFinal = inicio + timedelta(days=dias_totales)
        self.price = self.membresia.price * mult * (Decimal('1') - disc / Decimal('100'))
        super().save(*args, **kwargs)

    def clean(self):
        if MembresiaAsignada.objects.filter(miembro=self.miembro,
                                            dateInitial__lte=self.dateFinal,
                                            dateFinal__gte=self.dateInitial).exclude(pk=self.pk).exists():
            raise ValidationError('Ya existe una membresia asignada para este usuario en el rango de fechas indicado')
   
    @property
    def activa(self):
        hoy = date.today()
        return self.dateInitial <= hoy <= self.dateFinal

    @property
    def total_pagado(self):
        return self.pagos.aggregate(total=Sum('monto'))['total'] or Decimal('0')

    @property
    def saldo_pendiente(self):
        return self.price - self.total_pagado

    @property
    def estado_pago(self):
        if self.total_pagado >= self.price:
            return 'paid'
        elif self.total_pagado > 0:
            return 'partial'
        return 'pending'

    def __str__(self):
        return f"{self.miembro.name} - {self.miembro.lastname} - {self.membresia.name}"


  