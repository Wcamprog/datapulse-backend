import datetime
import math
from django.db import transaction
from apps.countries.models import Country, EconomicIndicator, ExchangeRate
from .models import IndiceRiesgo


class RiskCalculationService:

    @classmethod
    def calculate_all_indices(cls):
        paises_activos = Country.objects.filter(activo=True)
        registros_creados = 0

        with transaction.atomic():
            for pais in paises_activos:
                score_eco = cls._calcular_score_economico(pais)
                score_camb = cls._calcular_score_cambiario(pais)
                score_estabilidad = cls._calcular_score_estabilidad(pais)

                indice_compuesto = round( (score_eco * 0.40) + (score_camb * 0.30) + (score_estabilidad * 0.30), 2 )

                nivel = cls._determinar_nivel(indice_compuesto)

                detalle = {
                    "score_economico": score_eco,
                    "score_cambiario": score_camb,
                    "score_estabilidad": score_estabilidad,
                    "explicacion": "Cálculo basado en reglas de penalización oficiales"
                }

                IndiceRiesgo.objects.create(
                    pais=pais,
                    fecha_calculo=datetime.date.today(),
                    score_economico=score_eco,
                    score_cambiario=score_camb,
                    score_estabilidad=score_estabilidad,
                    indice_compuesto=indice_compuesto,
                    nivel_riesgo=nivel,
                    detalle_calculo=detalle
                )
                registros_creados += 1

        return True, f"Se calcularon y guardaron los índices de riesgo exactos para {registros_creados} países."

    @classmethod
    def _obtener_ultimo_indicador(cls, pais, tipo):
        """Función auxiliar para traer el último valor del Banco Mundial"""
        ind = EconomicIndicator.objects.filter(pais=pais, tipo=tipo).order_by('-anio').first()
        return ind.valor if ind else None

    @classmethod
    def _calcular_score_economico(cls, pais):
        score = 100

        # PIB per capita (penalizar si es bajo)
        pib_pc = cls._obtener_ultimo_indicador(pais, 'PIB_PERCAPITA')
        if pib_pc is not None:
            if pib_pc < 3000:
                score -= 30
            elif pib_pc < 6000:
                score -= 15
            elif pib_pc < 12000:
                score -= 5

        inflacion = cls._obtener_ultimo_indicador(pais, 'INFLACION')
        if inflacion is not None:
            if inflacion > 50:
                score -= 40
            elif inflacion > 10:
                score -= 25
            elif inflacion > 5:
                score -= 10

        desempleo = cls._obtener_ultimo_indicador(pais, 'DESEMPLEO')
        if desempleo is not None:
            if desempleo > 15:
                score -= 25
            elif desempleo > 10:
                score -= 15
            elif desempleo > 7:
                score -= 5

        deuda = cls._obtener_ultimo_indicador(pais, 'DEUDA_PIB')
        if deuda is not None:
            if deuda > 80:
                score -= 20
            elif deuda > 50:
                score -= 10

        return max(0, score)

    @classmethod
    def _calcular_score_cambiario(cls, pais):
        depreciacion = 0
        score = 100
        tasas = list(ExchangeRate.objects.filter(moneda_origen=pais.moneda_codigo).order_by('-fecha')[:30])

        if len(tasas) >= 2:
            tasa_nueva = tasas[0].tasa
            tasa_antigua = tasas[-1].tasa

            if tasa_antigua > 0:
                depreciacion = ((tasa_nueva - tasa_antigua) / tasa_antigua) * 100
                if depreciacion > 10:
                    score -= 30
                elif depreciacion > 5:
                    score -= 15
                elif depreciacion > 2:
                    score -= 5

            volatilidad = abs(depreciacion / len(tasas)) if tasa_antigua > 0 else 0
            if volatilidad > 3.0:
                score -= 40
            elif volatilidad > 1.5:
                score -= 25
            elif volatilidad > 0.5:
                score -= 10

        return max(0, score)

    @classmethod
    def _calcular_score_estabilidad(cls, pais):
        score = 100

        balanza = cls._obtener_ultimo_indicador(pais, 'BALANZA_COMERCIAL')
        if balanza is not None:
            if balanza < -10:
                score -= 25
            elif balanza < -5:
                score -= 15
            elif balanza < 0:
                score -= 5

        pib_qs = EconomicIndicator.objects.filter(pais=pais, tipo='PIB').order_by('-anio')[:2]
        if len(pib_qs) == 2:
            pib_actual = pib_qs[0].valor
            pib_anterior = pib_qs[1].valor
            if pib_anterior and pib_anterior > 0:
                crecimiento = ((pib_actual - pib_anterior) / pib_anterior) * 100
                if crecimiento < -2:
                    score -= 30
                elif crecimiento < 0:
                    score -= 20
                elif crecimiento < 1:
                    score -= 10

        indicadores_negativos = 0
        infl = cls._obtener_ultimo_indicador(pais, 'INFLACION')
        if infl and infl > 10: indicadores_negativos += 1
        des = cls._obtener_ultimo_indicador(pais, 'DESEMPLEO')
        if des and des > 10: indicadores_negativos += 1
        if balanza and balanza < 0: indicadores_negativos += 1

        score -= (indicadores_negativos * 5)

        return max(0, score)

    @classmethod
    def _determinar_nivel(cls, score):
        if score >= 75:
            return 'BAJO'
        elif score >= 50:
            return 'MODERADO'
        elif score >= 25:
            return 'ALTO'
        else:
            return 'CRITICO'