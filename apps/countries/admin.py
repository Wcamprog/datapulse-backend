from django.contrib import admin
from .models import Country, EconomicIndicator, ExchangeRate

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('codigo_iso', 'nombre', 'moneda_codigo', 'region', 'activo')
    search_fields = ('codigo_iso', 'nombre')

@admin.register(EconomicIndicator)
class EconomicIndicatorAdmin(admin.ModelAdmin):
    list_display = ('pais', 'tipo', 'anio', 'valor')
    list_filter = ('tipo', 'anio')

@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ('moneda_origen', 'moneda_destino', 'tasa', 'fecha')