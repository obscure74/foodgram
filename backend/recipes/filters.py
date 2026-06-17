import django_filters
from .models import Recipe, Tag


class RecipeFilter(django_filters.FilterSet):
    """Кастомный фильтр для рецептов."""

    # Фильтрация по тегам (по slug, логика "ИЛИ")
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        conjoined=False  # Логика "ИЛИ"
    )

    # Фильтрация по автору
    author = django_filters.NumberFilter(field_name='author__id')

    # Фильтрация по наличию в избранном
    is_favorited = django_filters.CharFilter(method='filter_is_favorited')

    # Фильтрация по наличию в списке покупок
    is_in_shopping_cart = django_filters.CharFilter(method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ['tags', 'author', 'is_favorited', 'is_in_shopping_cart']

    def filter_is_favorited(self, queryset, name, value):
        """Фильтр по избранному (принимает 1 или 0)."""
        if not self.request.user.is_authenticated:
            return queryset

        if value in ['1', 'true', 'True']:
            return queryset.filter(favorites__user=self.request.user)
        elif value in ['0', 'false', 'False']:
            return queryset.exclude(favorites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтр по списку покупок (принимает 1 или 0)."""
        if not self.request.user.is_authenticated:
            return queryset

        if value in ['1', 'true', 'True']:
            return queryset.filter(shopping_cart__user=self.request.user)
        elif value in ['0', 'false', 'False']:
            return queryset.exclude(shopping_cart__user=self.request.user)
        return queryset
