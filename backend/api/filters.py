import django_filters
from recipes.models import Recipe, Tag, Ingredient

class IngredientFilter(django_filters.FilterSet):
    """Фильтр для ингредиентов: поиск по параметру 'name' с начала строки."""
    name = django_filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']


class RecipeFilter(django_filters.FilterSet):
    """Кастомный фильтр для рецептов."""
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        conjoined=False
    )
    author = django_filters.NumberFilter(field_name='author__id')
    is_favorited = django_filters.CharFilter(method='filter_is_favorited')
    is_in_shopping_cart = django_filters.CharFilter(method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ['tags', 'author', 'is_favorited', 'is_in_shopping_cart']

    def filter_is_favorited(self, queryset, name, value):
        """Фильтр по избранному с учетом анонимов и значения 0."""
        user = self.request.user
        if value in ('1', 'true', 'True'):
            if user.is_authenticated:
                return queryset.filter(favorites__user=user)
            return queryset.none()  # У анонима избранного нет, возвращаем пусто

        if value in ('0', 'false', 'False'):
            if user.is_authenticated:
                return queryset.exclude(favorites__user=user)
            return queryset  # У анонима всё "не в избранном", возвращаем всё

        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтр по корзине с учетом анонимов и значения 0."""
        user = self.request.user
        if value in ('1', 'true', 'True'):
            if user.is_authenticated:
                return queryset.filter(shopping_cart__user=user)
            return queryset.none()

        if value in ('0', 'false', 'False'):
            if user.is_authenticated:
                return queryset.exclude(shopping_cart__user=user)
            return queryset

        return queryset
