from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'nombre_completo', 'rol', 'fecha_creacion', 'activo']
        read_only_fields = ['id', 'fecha_creacion', 'activo', 'rol']

class RegisterSerializer(serializers.ModelSerializer):
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