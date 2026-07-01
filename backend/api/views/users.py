from django.contrib.auth import get_user_model
from django.db.models import Count
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.serializers.users import (AvatarSerializer,
                                   SubscriptionAuthorSerializer)
from recipes.models import Subscription

User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    """ViewSet для кастомной модели User."""

    http_method_names = ['get', 'post', 'put', 'delete']
    lookup_field = 'pk'

    queryset = User.objects.annotate(
        recipes_count=Count('recipes')
    ).order_by(*User._meta.ordering)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated])
    def me(self, request):
        """Метод для me/ (GET)."""
        return super().me(request)

    @action(
        methods=['get'],
        detail=False,
        url_path='subscriptions',
        permission_classes=[IsAuthenticated],
        serializer_class=SubscriptionAuthorSerializer)
    def subscriptions(self, request):
        """Метод для получения подписок (GET)."""
        return self.get_paginated_response(
            SubscriptionAuthorSerializer(
                self.paginate_queryset(
                    User.objects.filter(
                        author_subscriptions__user=request.user)),
                many=True,
                context={'request': request}).data)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        """Подписка / отписка на автора."""

        user = request.user
        if request.method == 'DELETE':
            get_object_or_404(
                Subscription,
                user=user,
                author_id=pk).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        author = get_object_or_404(User, pk=pk)
        if user == author:
            raise ValidationError('Нельзя подписаться на самого себя')
        _, created = Subscription.objects.get_or_create(
            user=user,
            author=author)
        if not created:
            raise ValidationError(
                f'Уже подписаны на {author.username}')
        return Response(SubscriptionAuthorSerializer(
            author,
            context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED)

    @action(
        methods=['put', 'delete'],
        detail=False,
        url_path='me/avatar',
        permission_classes=[IsAuthenticated],
        serializer_class=AvatarSerializer)
    def avatar(self, request):

        if request.method == 'PUT':
            serializer = AvatarSerializer(
                request.user,
                data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        user = request.user
        user.avatar.delete()
        user.avatar = None
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)