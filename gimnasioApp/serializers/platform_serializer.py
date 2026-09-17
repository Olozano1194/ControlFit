from rest_framework import serializers
from ..models.gym_model import Gimnasio
from ..models.user_model import Usuario
from ..models.member_model import UsuarioGym
from ..models.payment_model import PagoMembresia
from ..models.demo_model import DemoRequest



class GimnasioCreadoSerializer(serializers.ModelSerializer):
    """Serializer anidado para gym_creado en DemoRequest (read_only)."""
    class Meta:
        model = Gimnasio
        fields = ['id', 'name']
        read_only_fields = ['id', 'name']


class DemoRequestSerializer(serializers.ModelSerializer):
    gym_creado = GimnasioCreadoSerializer(read_only=True)
    email_sent = serializers.SerializerMethodField()
    
    class Meta:
        model = DemoRequest
        fields = '__all__'
        read_only_fields = ('id', 'fecha_solicitud', 'gym_creado')
    
    def get_email_sent(self, obj):
        # True si el gym fue creado y el email se intentó enviar
        # Como es fire-and-forget, no podemos garantizar entrega
        # Retornamos True si gym_creado existe (email fue disparado)
        return obj.gym_creado is not None
    
    def validate_estado(self, value):
        """Reject modifications to cancelled requests."""
        if self.instance and self.instance.estado == 'cancelada':
            raise serializers.ValidationError("No se puede modificar una solicitud cancelada.")
        return value


# ============================================================
# PLATFORM — SUPERADMIN SERIALIZERS
# ============================================================

class PlatformStatsSerializer(serializers.Serializer):
    total_gimnasios = serializers.IntegerField()
    gimnasios_activos = serializers.IntegerField()
    total_usuarios_staff = serializers.IntegerField()
    demo_pendientes = serializers.IntegerField()
    demo_contactados = serializers.IntegerField()
    ingresos_mes_global = serializers.DecimalField(max_digits=14, decimal_places=2)
    miembros_activos_global = serializers.IntegerField()
    retencion_promedio = serializers.DecimalField(max_digits=5, decimal_places=1, coerce_to_string=False)


class UsuarioPlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'email', 'name', 'lastname', 'roles', 'is_active']


class MiembroActivoSerializer(serializers.ModelSerializer):
    membresia = serializers.CharField(source='membresia.name', read_only=True)
    dateFinal = serializers.DateField(format="%d-%m-%Y", read_only=True)
    saldo_pendiente = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = UsuarioGym
        fields = ['id', 'name', 'lastname', 'membresia', 'dateFinal', 'saldo_pendiente']


class PagoPlatformSerializer(serializers.ModelSerializer):
    miembro_name = serializers.CharField(source='membresia_asignada.miembro.name', read_only=True)
    miembro_lastname = serializers.CharField(source='membresia_asignada.miembro.lastname', read_only=True)
    membresia_name = serializers.CharField(source='membresia_asignada.membresia.name', read_only=True)

    class Meta:
        model = PagoMembresia
        fields = ['id', 'monto', 'fecha_pago', 'metodo_pago', 'miembro_name', 'miembro_lastname', 'membresia_name']


class GimnasioPlatformSerializer(serializers.ModelSerializer):
    usuarios_count = serializers.IntegerField(read_only=True)
    miembros_activos_count = serializers.IntegerField(read_only=True)
    ingresos_mes = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Gimnasio
        fields = ['id', 'name', 'address', 'phone', 'is_active', 'created_at',
                  'usuarios_count', 'miembros_activos_count', 'ingresos_mes']
        read_only_fields = ('id', 'created_at', 'usuarios_count', 'miembros_activos_count', 'ingresos_mes')


class GimnasioPlatformDetailSerializer(GimnasioPlatformSerializer):
    usuarios = UsuarioPlatformSerializer(many=True, read_only=True)
    miembros_activos = MiembroActivoSerializer(many=True, read_only=True)
    ultimos_pagos = PagoPlatformSerializer(many=True, read_only=True)

    class Meta(GimnasioPlatformSerializer.Meta):
        fields = GimnasioPlatformSerializer.Meta.fields + ['usuarios', 'miembros_activos', 'ultimos_pagos']


