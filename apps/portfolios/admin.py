from django.contrib import admin
from .models import Portafolio, Posicion

@admin.register(Portafolio)
class PortafolioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'usuario', 'activo', 'es_publico', 'fecha_creacion')
    list_filter = ('activo', 'es_publico')

@admin.register(Posicion)
class PosicionAdmin(admin.ModelAdmin):
    list_display = ('portafolio', 'pais', 'tipo_activo', 'monto_inversion_usd', 'fecha_entrada')