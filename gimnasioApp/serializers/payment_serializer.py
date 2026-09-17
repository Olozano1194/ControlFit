from rest_framework import serializers
from ..models import PagoMembresia



class PagoMembresiaSerializer(serializers.ModelSerializer):
    fecha_pago = serializers.DateTimeField(read_only=True, format="%Y-%m-%dT%H:%M:%S%z")

    class Meta:
        model = PagoMembresia
        fields = ['id', 'membresia_asignada', 'monto', 'fecha_pago', 'metodo_pago', 'nota']
        read_only_fields = ['id', 'fecha_pago', 'membresia_asignada']

    def validate_monto(self, value):
        if value <= 0:
            raise serializers.ValidationError("El monto debe ser mayor a cero")
        return value

    def validate(self, data):
        membresia = self.context.get('membresia_asignada') or data.get('membresia_asignada')
        if membresia:
            monto = data.get('monto')
            if monto and monto > membresia.saldo_pendiente:
                raise serializers.ValidationError({
                    'monto': f'El monto excede el saldo pendiente ({membresia.saldo_pendiente})'
                })
        return data

