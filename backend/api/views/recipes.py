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