import logging
from celery import shared_task
from django.contrib.auth import get_user_model
from apps.countries.services import DataSyncService
from apps.analytics.services import RiskCalculationService
from apps.analytics.models import Alerta
from apps.countries.models import Country

logger = logging.getLogger(__name__)
User = get_user_model()

@shared_task
def task_sincronizar_indicadores():
    logger.info("Iniciando Tarea: Sincronización del Banco Mundial...")
    msg = DataSyncService._sync_world_bank()
    pais_referencia = Country.objects.first()

    if pais_referencia:
        usuarios_activos = User.objects.filter(is_active=True)

        alertas_a_crear = [
            Alerta(
                usuario=user,
                pais=pais_referencia,
                tipo_alerta="INDICADOR",
                severidad="INFO",
                titulo="Sincronización Completa",
                mensaje=f"Nuevos datos económicos disponibles: {msg}"
            )
            for user in usuarios_activos
        ]

        Alerta.objects.bulk_create(alertas_a_crear)

    task_recalcular_riesgo.delay()
    return msg


@shared_task
def task_recalcular_riesgo():
    logger.info("Iniciando Tarea: Recálculo de IRPC...")

    exito, msg = RiskCalculationService.calculate_all_indices()
    return msg


@shared_task
def task_actualizar_tipos_cambio():
    logger.info("Iniciando Tarea: Tipos de cambio...")

    msg = DataSyncService._sync_exchange_rates()
    return msg