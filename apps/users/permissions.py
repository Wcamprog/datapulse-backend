from rest_framework.permissions import BasePermission
from .models import User

class EsAdminOSuperusuario(BasePermission):
    """
    Permite acceso si el usuario está autenticado y es ADMIN o superuser.
    """
    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        return bool(user.is_superuser or user.rol == User.Role.ADMIN)