from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PortafolioViewSet

router = DefaultRouter()
router.register(r'portafolios', PortafolioViewSet, basename='portafolio')

urlpatterns = [
    path('', include(router.urls)),
]