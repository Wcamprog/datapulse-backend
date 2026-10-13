from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['rol'] = user.rol
        token['is_superuser'] = user.is_superuser
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'nombre_completo': self.user.nombre_completo,
            'rol': self.user.rol,
            'is_superuser': self.user.is_superuser
            }
        return data

class UserSerializer(serializers.ModelSerializer):
    """Serializer para consulta de perfil / lectura general."""
    class Meta:
        model = User
        fields = ['id', 'email', 'nombre_completo', 'rol', 'fecha_creacion', 'activo', 'is_superuser']
        read_only_fields = ['id', 'fecha_creacion', 'activo', 'rol', 'is_superuser']


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer para autoregistro público (rol asignado automáticamente por defecto)."""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ['email', 'nombre_completo', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            nombre_completo=validated_data['nombre_completo'],
            password=validated_data['password']
        )
        return user


class AdminUserManageSerializer(serializers.ModelSerializer):
    """
    Serializer exclusivo para el Administrador:
    Permite crear y editar usuarios asignando rol y estado activo.
    """
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        validators=[validate_password]
    )

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'nombre_completo',
            'rol',
            'activo',
            'fecha_creacion',
            'password'
        ]
        read_only_fields = ['id', 'fecha_creacion']

    def validate_password(self, value):
        if not value:
            return None
        return value

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        rol = validated_data.get('rol', User.Role.VIEWER)

        is_staff = (rol == User.Role.ADMIN)

        user = User.objects.create_user(
            is_staff=is_staff,
            **validated_data
        )

        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        rol = validated_data.get('rol', instance.rol)

        if 'rol' in validated_data:
            instance.is_staff = (rol == User.Role.ADMIN)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance