from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from subscriptions.models import Subscription
from subscriptions.serializers import SubscriptionAuthorSerializer

from .serializers import CustomUserSerializer, CustomUserCreateSerializer

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet для пользователей."""
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        """Возвращает правильный сериализатор в зависимости от действия."""
        if self.action == 'create':
            return CustomUserCreateSerializer
        return CustomUserSerializer

    @action(detail=False, methods=['get', 'put', 'delete'],
            permission_classes=[IsAuthenticated], url_path='me')
    def me(self, request):
        """Получение/обновление/удаление текущего пользователя."""
        if request.method == 'GET':
            serializer = CustomUserSerializer(
                request.user, context={'request': request}
            )
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = CustomUserSerializer(
                request.user,
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        elif request.method == 'DELETE':
            request.user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['put', 'delete'],
            permission_classes=[IsAuthenticated], url_path='me/avatar')
    def avatar(self, request):
        """Добавление/удаление аватара."""
        if request.method == 'PUT':
            serializer = CustomUserSerializer(
                request.user,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            avatar_url = request.user.avatar.url if request.user.avatar else None
            return Response({'avatar': avatar_url})
        elif request.method == 'DELETE':
            request.user.avatar = None
            request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'],
            permission_classes=[IsAuthenticated], url_path='set_password')
    def set_password(self, request):
        """Смена пароля текущего пользователя."""
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not current_password or not new_password:
            return Response(
                {'detail': 'Поля current_password и new_password обязательны'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not request.user.check_password(current_password):
            return Response(
                {'detail': 'Неверный текущий пароль'},
                status=status.HTTP_400_BAD_REQUEST
            )

        request.user.set_password(new_password)
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        """Подписаться/отписаться от автора."""
        author = get_object_or_404(User, pk=pk)

        if request.user == author:
            return Response(
                {'errors': 'Нельзя подписаться на себя'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'POST':
            subscription, created = Subscription.objects.get_or_create(
                user=request.user,
                author=author
            )
            if not created:
                return Response(
                    {'errors': 'Вы уже подписаны на этого автора'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                SubscriptionAuthorSerializer(
                    author,
                    context={'request': request}
                ).data,
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            subscription = get_object_or_404(
                Subscription,
                user=request.user,
                author=author
            )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """Получить список подписок."""
        subscribed_authors = User.objects.filter(
            subscribers__user=request.user
        )

        page = self.paginate_queryset(subscribed_authors)
        if page is not None:
            serializer = SubscriptionAuthorSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionAuthorSerializer(
            subscribed_authors,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
