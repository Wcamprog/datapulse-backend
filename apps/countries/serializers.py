from rest_framework import serializers
from .models import Country, EconomicIndicator, ExchangeRate

class EconomicIndicatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = EconomicIndicator
        fields = '__all__'

class CountrySerializer(serializers.ModelSerializer):
    indicadores = EconomicIndicatorSerializer(many=True, read_only=True)
    class Meta:
        model = Country
        fields = '__all__'

class ExchangeRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRate
        fields = '__all__'