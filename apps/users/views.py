from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView

from core.pagination import StandardResultsSetPagination
from .serializers import AdminUserManageSerializer, CustomTokenObtainPairSerializer, UserSerializer, RegisterSerializer
from .permissions import EsAdminOSuperusuario

User = get_user_model()

@extend_schema(summary="Registro de usuario", description="Registro de usuario")
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

    @extend_schema(summary="Perfil de usuario", description="Perfil del usuario autenticado")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary="Actualizar perfil", description="Actualizar perfil")
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(exclude=True)
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

@extend_schema(exclude=True, tags=['Administración de Usuarios'])
class UserManagementViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-fecha_creacion')
    serializer_class = AdminUserManageSerializer
    permission_classes = [IsAuthenticated, EsAdminOSuperusuario]
    pagination_class = StandardResultsSetPagination


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer