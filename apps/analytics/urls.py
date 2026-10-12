from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IndiceRiesgoViewSet, AlertaViewSet, DashboardViewSet

router = DefaultRouter()
router.register(r'riesgo', IndiceRiesgoViewSet, basename='riesgo')
router.register(r'alertas', AlertaViewSet, basename='alerta')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

urlpatterns = [
    path('', include(router.urls)),
]