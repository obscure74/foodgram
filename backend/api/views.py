from django.db.models import Sum
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.filters import IngredientSearchFilter, RecipeFilter
from api.permissions import IsAuthorOrReadOnly
from api.serializers.common import ShortRecipeSerializer
from api.serializers.recipes import (IngredientSerializer,
                                     RecipeReadSerializer,
                                     RecipeWriteSerializer, TagSerializer)
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from recipes.services.shopping_list import generate_shopping_list
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

class TagViewSet(ReadOnlyModelViewSet):
    """ViewSet для чтения тэгов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    """ViewSet для чтения продуктов."""

    all_ingredients = Ingredient.objects.all()
    queryset = all_ingredients
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (IngredientSearchFilter,)
    search_fields = ('^name', 'name')


class RecipeViewSet(ModelViewSet):
    """ViewSet для рецептов."""

    queryset = Recipe.objects.all().prefetch_related(
        'favorites',
        'shoppingcarts',
    )

    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    http_method_names = ['get', 'post', 'patch', 'delete']

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от action."""
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def add_to_relation(self, model, request, pk):
        """Добавление рецепта в избранное/корзину."""
        recipe = get_object_or_404(Recipe, pk=pk)
        _, created = model.objects.get_or_create(
            user=request.user,
            recipe=recipe)
        if not created:
            raise ValidationError({
                'errors': (
                    f'Рецепт "{recipe.name}" уже добавлен '
                    f'в "{model._meta.verbose_name}".')
            })
        return Response(
            ShortRecipeSerializer(recipe).data,
            status=status.HTTP_201_CREATED)

    def remove_recipe_relation(self, model, request, pk):
        """Удаление рецепта из избранного/корзины."""
        get_object_or_404(model, user=request.user, recipe_id=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post', 'delete'],
            detail=True,
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        """Добавление/удаление рецепта из избранного."""

        if request.method == 'POST':
            return self.add_to_relation(Favorite, request, pk)
        return self.remove_recipe_relation(Favorite, request, pk)

    @action(methods=['post', 'delete'],
            detail=True,
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        """Добавление/удаление рецепта из корзины."""
        if request.method == 'POST':
            return self.add_to_relation(
                ShoppingCart,
                request,
                pk)
        return self.remove_recipe_relation(
            ShoppingCart,
            request,
            pk)

    @action(methods=['get'],
            detail=False,
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """Скачать список покупок."""
        ingredients = (
            RecipeIngredient.objects
            .filter(recipe__shoppingcarts__user=request.user)
            .values(
                'ingredient__name',
                'ingredient__measurement_unit',
                'recipe__name',
                'recipe__author__username',)
            .annotate(amount=Sum('amount'))
            .order_by('ingredient__name'))
        content = generate_shopping_list(
            user=request.user,
            ingredients_qs=ingredients)

        return FileResponse(
            content,
            as_attachment=True,
            filename='shopping_list.txt',
            content_type='text/plain',
        )

    @action(
        detail=True,
        methods=['get'],
        url_path='get_link',
        url_name='short-link')
    def get_link(self, request, pk=None):
        """Получение короткой ссылки на рецепт."""
        if not Recipe.objects.filter(pk=pk).exists():
            raise Http404('Рецепт не найден.')
        return Response({'short-link': request.build_absolute_uri(
            reverse('recipe-short-link', args=[pk]))
        })
    
