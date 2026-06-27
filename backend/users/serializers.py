import re
from django.contrib.auth import get_user_model
from rest_framework import serializers
from subscriptions.models import Subscription

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
        return Subscription.objects.filter(
            user=request.user, author=obj
        ).exists()


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

    def validate_username(self, value):
        """Валидация username по regex ^[\w.@+-]+\Z"""
        if not re.match(r'^[\w.@+-]+\Z', value):
            raise serializers.ValidationError(
                'Для поля `username` не должны приниматься значения, не соответствующие регулярному выражению ^[\\w.@+-]+\\Z'
            )
        return value

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
