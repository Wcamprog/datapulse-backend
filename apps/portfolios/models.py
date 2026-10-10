from django.db import models
from django.db.models import Q, F
from django.conf import settings
from apps.countries.models import Country

class Portafolio(models.Model):
    nombre = models.CharField(max_length=225)
    descripcion = models.CharField(max_length=500, blank=True, null=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='portafolios')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)
    es_publico = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['usuario', 'nombre'], name='unique_portafolio_per_user')
        ]

    def __str__(self):
        return f"{self.nombre} - {self.usuario.email}"


class Posicion(models.Model):
    class AssetType(models.TextChoices):
        RENTA_FIJA = 'RENTA_FIJA', 'Renta Fija'
        RENTA_VARIABLE = 'RENTA_VARIABLE', 'Renta Variable'
        COMMODITIES = 'COMMODITIES', 'Commodities'
        MONEDA = 'MONEDA', 'Moneda'

    portafolio = models.ForeignKey(Portafolio, on_delete=models.CASCADE, related_name='posiciones')
    pais = models.ForeignKey(Country, on_delete=models.PROTECT, related_name='posiciones')
    tipo_activo = models.CharField(max_length=20, choices=AssetType.choices)
    monto_inversion_usd = models.DecimalField(max_digits=15, decimal_places=2)
    fecha_entrada = models.DateField()
    fecha_salida = models.DateField(null=True, blank=True)
    notas = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(fecha_salida__isnull=True) | Q(fecha_salida__gt=F('fecha_entrada')),
                name='check_fecha_salida_mayor_entrada'
            )
        ]

    def __str__(self):
        return f"{self.tipo_activo} en {self.pais.codigo_iso} - {self.monto_inversion_usd} USD"