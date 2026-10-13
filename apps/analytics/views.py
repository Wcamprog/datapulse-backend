from django.db.models import Avg
from datetime import datetime
from drf_spectacular.types import OpenApiTypes
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from .models import IndiceRiesgo, Alerta
from .serializers import IndiceRiesgoSerializer, AlertaSerializer
from .services import RiskCalculationService
from apps.portfolios.models import Portafolio
from apps.countries.models import Country, EconomicIndicator


@extend_schema_view(
    list=extend_schema(summary="Ranking de riesgo", description="Ranking de paises por indice de riesgo"),
    retrieve=extend_schema(summary="Detalle de riesgo", description="Detalle de riesgo de un pais con historico"),
    create=extend_schema(exclude=True), update=extend_schema(exclude=True),
    partial_update=extend_schema(exclude=True), destroy=extend_schema(exclude=True)
)
class IndiceRiesgoViewSet(viewsets.ModelViewSet):
    queryset = IndiceRiesgo.objects.all().order_by('-indice_compuesto')
    serializer_class = IndiceRiesgoSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pais__codigo_iso'

    @extend_schema(summary="Histórico de riesgo", description="Histórico de índices para un país por código ISO")
    @action(detail=False, methods=['get'], url_path='historico/(?P<codigo_iso>[^/.]+)')
    def historico(self, request, codigo_iso=None):
        """
        Retorna todos los cálculos de riesgo históricos para el país especificado
        ordenados desde el más reciente al más antiguo.
        """
        registros = IndiceRiesgo.objects.filter(
            pais__codigo_iso__iexact=codigo_iso
        ).order_by('-fecha_calculo')

        serializer = self.get_serializer(registros, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Recalcular índices",
        description="Recalcular indices para todos los paises (solo ADMIN)",
        request=None,
        responses={200: OpenApiTypes.OBJECT}
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def calcular(self, request):
        exito, mensaje = RiskCalculationService.calculate_all_indices()

        if exito:
            return Response({"mensaje": mensaje}, status=status.HTTP_200_OK)
        return Response({"error": "Fallo al calcular los índices"}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(summary="Listar alertas", description="Alertas del usuario (filtro: leidas/no leidas, tipo)"),
    create=extend_schema(exclude=True), retrieve=extend_schema(exclude=True),
    update=extend_schema(exclude=True), partial_update=extend_schema(exclude=True),
    destroy=extend_schema(exclude=True)
)
class AlertaViewSet(viewsets.ModelViewSet):
    serializer_class = AlertaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Alerta.objects.filter(usuario=self.request.user)

    @extend_schema(summary="Marcar como leída", description="Marcar como leida")
    @action(detail=True, methods=['put'])
    def leer(self, request, pk=None):
        alerta = self.get_object()
        alerta.leida = True
        alerta.save()
        return Response({"mensaje": "Alerta marcada como leída"})

    @extend_schema(summary="Marcar todas leídas", description="Marcar todas como leídas")
    @action(detail=False, methods=['put'], url_path='leer-todas')
    def leer_todas(self, request):
        Alerta.objects.filter(usuario=self.request.user, leida=False).update(leida=True)
        return Response({"mensaje": "Todas las alertas marcadas como leídas"})

    @extend_schema(summary="Resumen de alertas", description="Conteo por tipo y severidad")
    @action(detail=False, methods=['get'])
    def resumen(self, request):
        return Response({"mensaje": "Endpoint resumen alertas preparado"})


class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="KPIs globales",
        description="KPIs globales (total países, alertas activas, portafolios del usuario, promedio IRPC región)"
    )
    @action(detail=False, methods=['get'])
    def resumen(self, request):
        total_paises = Country.objects.filter(activo=True).count()

        alertas_activas = Alerta.objects.filter(leida=False).filter(
            usuario__in=[request.user, None]
        ).count()

        total_portafolios = Portafolio.objects.filter(
            usuario=request.user,
            activo=True
        ).count()

        promedio_irpc = IndiceRiesgo.objects.aggregate(
            promedio=Avg('indice_compuesto')
        )['promedio'] or 0.0

        data = {
            "total_paises": total_paises,
            "alertas_activas": alertas_activas,
            "total_portafolios": total_portafolios,
            "promedio_irpc": round(float(promedio_irpc), 2)
        }

        return Response(data)

    @extend_schema(
        summary="Datos para mapa",
        description="Países con coordenadas, índice de riesgo compuesto (IRPC), nivel y color"
    )
    @action(detail=False, methods=['get'])
    def mapa(self, request):
        paises = Country.objects.filter(activo=True)
        colores_nivel = {
            'BAJO': '#10b981',
            'MODERADO': '#f59e0b',
            'ALTO': '#f97316',
            'CRITICO': '#ef4444'
        }

        resultado = []
        for pais in paises:
            ultimo_riesgo = IndiceRiesgo.objects.filter(pais=pais).order_by('-fecha_calculo').first()

            score = round(float(ultimo_riesgo.indice_compuesto), 1) if ultimo_riesgo else None
            nivel = ultimo_riesgo.nivel_riesgo if ultimo_riesgo else 'SIN_DATOS'
            color = colores_nivel.get(nivel, '#94a3b8')

            resultado.append({
                "codigo_iso": pais.codigo_iso,
                "nombre": pais.nombre,
                "region": getattr(pais, 'region', ''),
                "latitud": float(pais.latitud) if pais.latitud is not None else 0.0,
                "longitud": float(pais.longitud) if pais.longitud is not None else 0.0,
                "irpc": score,
                "nivel": nivel,
                "color": color
            })

        return Response(resultado)

    @extend_schema(
        summary="Tendencias históricas",
        description="Evolución de un indicador para países seleccionados en los últimos 5 años",
        parameters=[
            OpenApiParameter(name='tipo', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY,
                             description='Tipo de indicador (PIB, INFLACION, DESEMPLEO, etc.)'),
            OpenApiParameter(name='paises', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY,
                             description='Códigos ISO separados por coma (ej: CO,BR,MX)')
        ]
    )
    @action(detail=False, methods=['get'])
    def tendencias(self, request):
        tipo_indicador = request.query_params.get('tipo', 'PIB').upper()
        paises_param = request.query_params.get('paises', 'CO,BR,MX')
        codigos_iso = [iso.strip().upper() for iso in paises_param.split(',') if iso.strip()]

        anios_disponibles = list(
            EconomicIndicator.objects.filter(tipo=tipo_indicador)
            .values_list('anio', flat=True)
            .distinct()
            .order_by('-anio')[:5]
        )
        anios_disponibles.sort()

        if not anios_disponibles:
            anio_actual = datetime.now().year
            anios_disponibles = [anio_actual - i for i in reversed(range(5))]

        series = []
        for iso in codigos_iso:
            pais = Country.objects.filter(codigo_iso=iso).first()
            if not pais:
                continue

            valores = []
            for anio in anios_disponibles:
                ind = EconomicIndicator.objects.filter(pais=pais, tipo=tipo_indicador, anio=anio).first()
                valores.append(float(ind.valor) if ind else 0.0)

            series.append({
                "codigo_iso": pais.codigo_iso,
                "nombre": pais.nombre,
                "valores": valores
            })

        return Response({
            "indicador": tipo_indicador,
            "anios": anios_disponibles,
            "series": series
        })

