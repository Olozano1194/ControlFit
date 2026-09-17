from rest_framework import serializers
from ..models.calendar_model import TipoEvento, EventoCalendario



class TipoEventoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoEvento
        fields = ['id', 'nombre', 'color', 'gimnasio', 'created_at']
        read_only_fields = ('id', 'gimnasio', 'created_at')


class TipoEventoSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoEvento
        fields = ['id', 'nombre', 'color']


class EventoCalendarioSerializer(serializers.ModelSerializer):
    tipo_detalle = TipoEventoSimpleSerializer(source='tipo', read_only=True)
    descripcion = serializers.CharField(required=False, allow_blank=True, allow_null=True, default='')

    class Meta:
        model = EventoCalendario
        fields = ['id', 'titulo', 'fecha_inicio', 'fecha_fin', 'descripcion',
                  'tipo', 'tipo_detalle', 'relacion_tipo', 'relacion_id',
                  'created_by', 'gimnasio', 'created_at']
        read_only_fields = ('id', 'gimnasio', 'created_by', 'created_at')

    def validate(self, data):
        inicio = data.get('fecha_inicio') or (self.instance.fecha_inicio if self.instance else None)
        fin = data.get('fecha_fin') or (self.instance.fecha_fin if self.instance else None)
        if inicio and fin and fin <= inicio:
            raise serializers.ValidationError("fecha_fin must be after fecha_inicio")
        # Normalize explicit null to '' only when the field is actually present.
        # On partial updates (PATCH) omitting descripcion, DRF skips the field,
        # so it must NOT be re-injected here or the stored value is erased.
        if 'descripcion' in data and data.get('descripcion') is None:
            data['descripcion'] = ''
        return data

