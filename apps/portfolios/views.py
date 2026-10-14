import datetime, io
from django.utils import timezone
from django.http import FileResponse
from django.db.models import Sum, Count
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema, extend_schema_view

from core.pagination import StandardResultsSetPagination
from .models import Portafolio, Posicion
from .serializers import PortafolioSerializer, PosicionSerializer


@extend_schema_view(
    list=extend_schema(summary="Listar portafolios", description="Listar portafolios del usuario + publicos"),
    create=extend_schema(summary="Crear portafolio", description="Crea un nuevo portafolio"),
    retrieve=extend_schema(summary="Detalle del portafolio", description="Detalle con posiciones y metricas"),
    update=extend_schema(summary="Actualizar portafolio", description="Actualizar portafolio"),
    partial_update=extend_schema(exclude=True),  # Ocultamos PATCH
    destroy=extend_schema(summary="Eliminar portafolio", description="Eliminar (soft delete)")
)
class PortafolioViewSet(viewsets.ModelViewSet):
    serializer_class = PortafolioSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Portafolio.objects.filter(usuario=self.request.user) | Portafolio.objects.filter(es_publico=True)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    def perform_destroy(self, instance):
        instance.activo = False
        instance.save()


    @extend_schema(summary="Agregar posición", description="Agregar posicion", request=PosicionSerializer)
    @action(detail=True, methods=['post'], url_path='posiciones')
    def agregar_posicion(self, request, pk=None):
        portafolio = self.get_object()
        serializer = PosicionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(portafolio=portafolio)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(methods=['PUT'], summary="Editar posición", description="Editar posicion")
    @extend_schema(methods=['DELETE'], summary="Cerrar posición", description="Cerrar posicion (set fecha_salida)")
    @action(detail=True, methods=['put', 'delete'], url_path=r'posiciones/(?P<posicion_id>\d+)')
    def detalle_posicion(self, request, pk=None, posicion_id=None):
        portafolio = self.get_object()
        try:
            posicion = Posicion.objects.get(id=posicion_id, portafolio=portafolio)
        except Posicion.DoesNotExist:
            return Response({"error": "Posición no encontrada"}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'PUT':
            serializer = PosicionSerializer(posicion, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            if posicion.fecha_salida is not None:
                return Response(
                    {"error": f"La posición ya fue cerrada previamente el {posicion.fecha_salida}."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            hoy = timezone.localdate()

            if hoy < posicion.fecha_entrada:
                return Response(
                    {
                        "error": f"No se puede cerrar la posición: la fecha de entrada ({posicion.fecha_entrada}) es posterior a la fecha actual ({hoy})."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                posicion.fecha_salida = hoy
                posicion.save()
                return Response({"mensaje": "Posición cerrada exitosamente"}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response(
                    {"error": f"Error de integridad al cerrar la posición: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

    @extend_schema(summary="Resumen del portafolio", description="Resumen: distribucion por pais, tipo_activo, riesgo")
    @action(detail=True, methods=['get'], url_path='resumen')
    def resumen(self, request, pk=None):
        portafolio = self.get_object()
        posiciones = Posicion.objects.filter(portafolio=portafolio, fecha_salida__isnull=True)

        total_inversion = posiciones.aggregate(total=Sum('monto_inversion_usd'))['total'] or 0

        dist_activos = posiciones.values('tipo_activo').annotate(
            total=Sum('monto_inversion_usd'),
            cantidad=Count('id')
        )

        dist_paises = posiciones.values('pais__nombre').annotate(
            total=Sum('monto_inversion_usd')
        )

        return Response({
            "portafolio": portafolio.nombre,
            "total_invertido_usd": total_inversion,
            "distribucion_activos": dist_activos,
            "distribucion_paises": dist_paises
        })

    @extend_schema(summary="Exportar PDF", description="Exportar reporte PDF del portafolio")
    @action(detail=True, methods=['get'], url_path='export/pdf')
    def exportar_pdf(self, request, pk=None):
        portafolio = self.get_object()

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)

        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, 750, f"Reporte de Portafolio: {portafolio.nombre}")

        p.setFont("Helvetica", 12)
        p.drawString(50, 720, f"Descripción: {portafolio.descripcion}")
        p.drawString(50, 700, f"Fecha de creación: {portafolio.fecha_creacion.strftime('%Y-%m-%d')}")

        p.drawString(50, 660, "Posiciones Activas:")

        posiciones = Posicion.objects.filter(portafolio=portafolio, fecha_salida__isnull=True)
        y = 640
        for pos in posiciones:
            texto = f"- {pos.pais.nombre} | {pos.tipo_activo} | USD ${pos.monto_inversion_usd}"
            p.drawString(70, y, texto)
            y -= 20

            if y < 50:
                p.showPage()
                y = 750

        p.showPage()
        p.save()

        buffer.seek(0)

        return FileResponse(buffer, as_attachment=True, filename=f"reporte_{portafolio.id}.pdf")

    @extend_schema(summary="Exportar PDF", description="Exportar reporte PDF del portafolio")
    @action(detail=True, methods=['get'], url_path='export/pdf')
    def exportar_pdf(self, request, pk=None):
        portafolio = self.get_object()

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)

        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, 750, f"Reporte de Portafolio: {portafolio.nombre}")

        p.setFont("Helvetica", 12)
        p.drawString(50, 720, f"Descripción: {portafolio.descripcion}")
        p.drawString(50, 700, f"Fecha de creación: {portafolio.fecha_creacion.strftime('%Y-%m-%d')}")

        p.drawString(50, 660, "Posiciones Activas:")

        posiciones = Posicion.objects.filter(portafolio=portafolio, fecha_salida__isnull=True)
        y = 640
        for pos in posiciones:
            texto = f"- {pos.pais.nombre} | {pos.tipo_activo} | USD ${pos.monto_inversion_usd}"
            p.drawString(70, y, texto)
            y -= 20

            if y < 50:
                p.showPage()
                y = 750

        p.showPage()
        p.save()

        buffer.seek(0)

        return FileResponse(buffer, as_attachment=True, filename=f"reporte_{portafolio.id}.pdf")


@extend_schema_view(
    list=extend_schema(exclude=True), retrieve=extend_schema(exclude=True),
    create=extend_schema(exclude=True), update=extend_schema(exclude=True),
    partial_update=extend_schema(exclude=True), destroy=extend_schema(exclude=True)
)
class PosicionViewSet(viewsets.ModelViewSet):
    serializer_class = PosicionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Posicion.objects.filter(portafolio__usuario=self.request.user)