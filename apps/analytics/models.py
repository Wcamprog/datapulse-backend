from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.countries.models import Country

class IndiceRiesgo(models.Model):
    class NivelRiesgo(models.TextChoices):
        BAJO = 'BAJO', 'Bajo'
        MODERADO = 'MODERADO', 'Moderado'
        ALTO = 'ALTO', 'Alto'
        CRITICO = 'CRITICO', 'Crítico'

    pais = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='indices_riesgo')
    fecha_calculo = models.DateTimeField(auto_now_add=True)
    score_economico = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    score_cambiario = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    score_estabilidad = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    indice_compuesto = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    nivel_riesgo = models.CharField(max_length=20, choices=NivelRiesgo.choices)
    detalle_calculo = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(indice_compuesto__gte=0) & models.Q(indice_compuesto__lte=100),
                name='check_indice_compuesto_rango'
            )
        ]

    def __str__(self):
        return f"{self.pais.codigo_iso} - {self.nivel_riesgo} ({self.indice_compuesto})"


class Alerta(models.Model):
    class TipoAlerta(models.TextChoices):
        RIESGO = 'RIESGO', 'Riesgo'
        TIPO_CAMBIO = 'TIPO_CAMBIO', 'Tipo de Cambio'
        INDICADOR = 'INDICADOR', 'Indicador'

    class Severidad(models.TextChoices):
        INFO = 'INFO', 'Info'
        WARNING = 'WARNING', 'Warning'
        CRITICAL = 'CRITICAL', 'Critical'

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='alertas')
    pais = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='alertas')
    tipo_alerta = models.CharField(max_length=20, choices=TipoAlerta.choices)
    severidad = models.CharField(max_length=20, choices=Severidad.choices)
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.severidad}] {self.titulo}"


class LogActividad(models.Model):
    class Accion(models.TextChoices):
        CREAR = 'CREAR', 'Crear'
        EDITAR = 'EDITAR', 'Editar'
        ELIMINAR = 'ELIMINAR', 'Eliminar'
        CONSULTAR = 'CONSULTAR', 'Consultar'
        LOGIN = 'LOGIN', 'Login'
        EXPORT = 'EXPORT', 'Exportar'

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='logs')
    accion = models.CharField(max_length=20, choices=Accion.choices)
    entidad_afectada = models.CharField(max_length=100)
    entidad_id = models.CharField(max_length=50, null=True, blank=True)
    detalle = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario} - {self.accion} {self.entidad_afectada}"