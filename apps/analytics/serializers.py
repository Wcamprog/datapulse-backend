from rest_framework import serializers
from .models import IndiceRiesgo, Alerta

class IndiceRiesgoSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndiceRiesgo
        fields = '__all__'

class AlertaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alerta
        fields = '__all__'