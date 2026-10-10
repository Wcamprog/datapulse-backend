from django.db import models

class Country(models.Model):
    class Region(models.TextChoices):
        ANDINA = 'ANDINA', 'Andina'
        CONO_SUR = 'CONO_SUR', 'Cono Sur'
        CENTROAMERICA = 'CENTROAMERICA', 'Centroamérica'
        CARIBE = 'CARIBE', 'Caribe'

    codigo_iso = models.CharField(max_length=3, primary_key=True)
    nombre = models.CharField(max_length=100)
    moneda_codigo = models.CharField(max_length=3)
    moneda_nombre = models.CharField(max_length=50)
    region = models.CharField(max_length=20, choices=Region.choices)
    latitud = models.DecimalField(max_digits=9, decimal_places=6)
    longitud = models.DecimalField(max_digits=9, decimal_places=6)
    poblacion = models.BigIntegerField()
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} ({self.codigo_iso})"


class EconomicIndicator(models.Model):
    class IndicatorType(models.TextChoices):
        PIB = 'PIB', 'PIB'
        INFLACION = 'INFLACION', 'Inflación'
        DESEMPLEO = 'DESEMPLEO', 'Desempleo'
        BALANZA_COMERCIAL = 'BALANZA_COMERCIAL', 'Balanza Comercial'
        DEUDA_PIB = 'DEUDA_PIB', 'Deuda PIB'
        PIB_PERCAPITA = 'PIB_PERCAPITA', 'PIB Per Cápita'

    class Unit(models.TextChoices):
        PORCENTAJE = 'PORCENTAJE', 'Porcentaje'
        USD = 'USD', 'USD'
        USD_MILES_MILLONES = 'USD_MILES_MILLONES', 'USD Miles de Millones'

    class Source(models.TextChoices):
        WORLD_BANK = 'WORLD_BANK', 'World Bank'
        MANUAL = 'MANUAL', 'Manual'

    pais = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='indicadores')
    tipo = models.CharField(max_length=30, choices=IndicatorType.choices)
    valor = models.DecimalField(max_digits=15, decimal_places=4)
    unidad = models.CharField(max_length=20, choices=Unit.choices)
    anio = models.IntegerField()
    fuente = models.CharField(max_length=20, choices=Source.choices, default=Source.WORLD_BANK)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['pais', 'tipo', 'anio']

    def __str__(self):
        return f"{self.pais.codigo_iso} - {self.tipo} ({self.anio}): {self.valor}"

class ExchangeRate(models.Model):
    """"
      El documento sugería una relación directa hacia Pais.moneda_codigo.
      Sin embargo, en el disenio relacional de bases de datos, un Foreign Key requiere
      que el campo destino sea estrictamente único. Como varios países pueden compartir
      la misma moneda (como Ecuador y Panamá con el USD), moneda_codigo no puede ser único
      en la tabla País. Por lo tanto, desacoplé la relación a nivel de base de datos usando un CharField
      para la moneda, permitiendo almacenar el código libremente sin romper la integridad referencial"
    """
    moneda_origen = models.CharField(max_length=3)
    moneda_destino = models.CharField(max_length=3, default='USD')
    tasa = models.DecimalField(max_digits=15, decimal_places=6)
    fecha = models.DateField()
    variacion_porcentual = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    fuente = models.CharField(max_length=50, default='ExchangeRate-API')

    class Meta:
        unique_together = ['moneda_origen', 'moneda_destino', 'fecha']

    def __str__(self):
        return f"{self.moneda_origen}/{self.moneda_destino} - {self.fecha}: {self.tasa}"