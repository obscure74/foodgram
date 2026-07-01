import django_filters
from django_filters import rest_framework as filters
from rest_framework.filters import SearchFilter

from recipes.models import Recipe, Tag


class IngredientSearchFilter(SearchFilter):
    """Фильтр для поиска ингридентов по имени."""

    search_param = 'name'


class RecipeFilter(django_filters.FilterSet):
    """Фильтр для рецептов по автору."""

    available_tags = Tag.objects.all()
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=available_tags)

    author = django_filters.NumberFilter(
        field_name='author__id')

    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited')

    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart')

    class Meta:

        model = Recipe
        fields = ['tags', 'author', 'is_in_shopping_cart', 'is_favorited']

    def filter_is_in_shopping_cart(self, recipes, name, is_in_cart):
        """Для фильтрации рецептов по пользователю в покупках."""
        user = self.request.user
        if not user.is_authenticated:
            return recipes.none()
        if is_in_cart:
            return recipes.filter(
                shoppingcarts__user=user
            ).distinct()
        return recipes

    def filter_is_favorited(self, recipes, name, is_in_favorited):
        """Для фильтрации рецептов по пользователю в избранном."""
        user = self.request.user
        if not user.is_authenticated:
            return recipes.none()
        if is_in_favorited:
            return recipes.filter(
                favorites__user=user
            ).distinct()
        return recipes