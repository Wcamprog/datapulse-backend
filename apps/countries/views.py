from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from .models import Country, EconomicIndicator, ExchangeRate
from .serializers import CountrySerializer, EconomicIndicatorSerializer, ExchangeRateSerializer
from .services import DataSyncService

from drf_spectacular.types import OpenApiTypes

from core.pagination import StandardResultsSetPagination

@extend_schema_view(
    list=extend_schema(summary="Listar países", description="Listar paises (con filtros por region)"),
    retrieve=extend_schema(summary="Detalle de país", description="Detalle de pais con indicadores"),
    create=extend_schema(exclude=False), update=extend_schema(exclude=True), partial_update=extend_schema(exclude=True), destroy=extend_schema(exclude=True)
)
class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Indicadores de un país", description="Indicadores de un pais (filtro por tipo, anio)")
    @action(detail=True, methods=['get'])
    def indicadores(self, request, pk=None):
        pais = self.get_object()
        indicadores_pais = EconomicIndicator.objects.filter(pais=pais)
        serializer = EconomicIndicatorSerializer(indicadores_pais, many=True)
        return Response(serializer.data)

    @extend_schema(summary="Histórico tipo de cambio", description="Historico tipo de cambio (filtro por rango de fechas)")
    @action(detail=True, methods=['get'], url_path='tipo-cambio')
    def tipo_cambio(self, request, pk=None):
        pais = self.get_object()
        tasas = ExchangeRate.objects.filter(moneda_origen=pais.moneda_codigo)
        serializer = ExchangeRateSerializer(tasas, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Sincronizar indicadores",
        description="Disparar sincronización desde APIs externas (solo ADMIN)",
        request=None,
        responses={200: OpenApiTypes.OBJECT}
    )
    @action(detail=False, methods=['post'], url_path='sync-indicadores', permission_classes=[IsAdminUser])
    def sync_indicadores(self, request):
        exito, mensaje = DataSyncService.sync_all()

        if exito:
            return Response({"mensaje": mensaje}, status=status.HTTP_200_OK)
        else:
            return Response({"error": mensaje}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    @extend_schema(
        summary="Consultar datos de país externo",
        description="Consulta REST Countries v5 para autocompletar campos antes de guardar",
        parameters=[
            OpenApiParameter(name='query', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY,
                             description='Nombre o ISO del país')
        ]
    )
    @action(detail=False, methods=['get'], url_path='consultar-externo')
    def consultar_externo(self, request):
        query = request.query_params.get('query')
        if not query:
            return Response({"error": "Debe proporcionar el parámetro 'query'."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            datos = DataSyncService.consultar_pais_externo(query)
            return Response(datos, status=status.HTTP_200_OK)
        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Error al consultar la API externa: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema_view(
    list=extend_schema(exclude=True),
    retrieve=extend_schema(exclude=True),
    create=extend_schema(exclude=True),
    update=extend_schema(exclude=True),
    partial_update=extend_schema(exclude=True),
    destroy=extend_schema(exclude=True)
)
class EconomicIndicatorViewSet(viewsets.ModelViewSet):
    queryset = EconomicIndicator.objects.all()
    serializer_class = EconomicIndicatorSerializer
    permission_classes = [IsAuthenticated]


@extend_schema_view(
    list=extend_schema(exclude=True),
    retrieve=extend_schema(exclude=True),
    create=extend_schema(exclude=True),
    update=extend_schema(exclude=True),
    partial_update=extend_schema(exclude=True),
    destroy=extend_schema(exclude=True)
)
class ExchangeRateViewSet(viewsets.ModelViewSet):
    queryset = ExchangeRate.objects.all()
    serializer_class = ExchangeRateSerializer
    permission_classes = [IsAuthenticated]