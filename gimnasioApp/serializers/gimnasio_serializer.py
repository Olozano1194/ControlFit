from rest_framework import serializers
from ..models import Gimnasio


class GimnasioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gimnasio
        fields = '__all__'
        read_only_fields = ('id', 'created_at')

