from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from subscriptions.models import Subscription
from subscriptions.serializers import SubscriptionAuthorSerializer

from .serializers import CustomUserSerializer

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet для пользователей."""
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [AllowAny]

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])

    def get_serializer_class(self):
        """Возвращает правильный сериализатор в зависимости от действия."""
        if self.action == 'create':
            from users.serializers import CustomUserCreateSerializer
            return CustomUserCreateSerializer
        return CustomUserSerializer

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
                    context={
                        'request': request}).data,
                status=status.HTTP_201_CREATED)

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
        # Получаем авторов, на которых подписан пользователь
        subscribed_authors = User.objects.filter(
            subscribers__user=request.user
        )

        # Пагинация
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
