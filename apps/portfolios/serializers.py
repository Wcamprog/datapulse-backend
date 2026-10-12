from rest_framework import serializers
from .models import Portafolio, Posicion

class PosicionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Posicion
        fields = '__all__'

class PortafolioSerializer(serializers.ModelSerializer):
    posiciones = PosicionSerializer(many=True, read_only=True)

    class Meta:
        model = Portafolio
        fields = '__all__'
        read_only_fields = ['usuario', 'fecha_creacion', 'fecha_modificacion']