from django.contrib.auth import get_user_model
from rest_framework import serializers
from djoser.serializers import TokenCreateSerializer as BaseTokenCreateSerializer

User = get_user_model()


class CustomUserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели пользователя."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
        )
        read_only_fields = ('id',)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.followers.filter(user=request.user).exists()


class CustomUserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания пользователя."""

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
        )
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class CustomTokenCreateSerializer(BaseTokenCreateSerializer):
    """Кастомный сериализатор для аутентификации по email."""

    def validate(self, attrs):
        # Djoser использует email как LOGIN_FIELD
        email = attrs.get('email')
        password = attrs.get('password')

        if not email or not password:
            raise serializers.ValidationError({
                'non_field_errors': ['Невозможно войти с предоставленными учетными данными.']
            })

        # Ищем пользователя по email
        user = User.objects.filter(email=email).first()

        if not user or not user.check_password(password):
            raise serializers.ValidationError({
                'non_field_errors': ['Невозможно войти с предоставленными учетными данными.']
            })

        if not user.is_active:
            raise serializers.ValidationError({
                'non_field_errors': ['Пользователь не активен.']
            })

        attrs['user'] = user
        return attrs
