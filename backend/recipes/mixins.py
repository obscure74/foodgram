from django.contrib import admin


class RecipesCountMixin:
    """Миксин для подсчёта рецептов."""

    list_display = ('get_recipes_count',)

    @admin.display(description='Рецептов')
    def get_recipes_count(self, instance):
        return instance.recipes.count()