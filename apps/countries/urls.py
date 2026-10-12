from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CountryViewSet, EconomicIndicatorViewSet, ExchangeRateViewSet

router = DefaultRouter()
router.register(r'paises', CountryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]