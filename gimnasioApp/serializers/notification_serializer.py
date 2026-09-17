from rest_framework import serializers
from ..models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'tipo', 'titulo', 'mensaje', 'fecha', 'relacion_tipo',
                  'relacion_id', 'link', 'whatsapp_link', 'is_read', 'read_at', 'created_at']
        read_only_fields = ('id', 'gimnasio', 'is_read', 'read_at', 'created_at')