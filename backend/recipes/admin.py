from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from django.utils.safestring import mark_safe

from recipes.filters import (CookingTimeFilter, HasFollowersFilter,
                             HasRecipesFilter, HasSubscriptionsFilter,
                             UsedInRecipesFilter)
from recipes.mixins import RecipesCountMixin
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Subscription, Tag, User)

admin.site.unregister(Group)


def render_image(obj, field, size=80):
    image = getattr(obj, field, None)
    if image:
        return mark_safe(
            f'<img src="{image.url}" width="{size}" />'
        )
    return '—'


@admin.register(Favorite, ShoppingCart)
class UserRecipeAdmin(admin.ModelAdmin):
    """Регистрация админки для Favorite и ShoppingCart."""

    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(User)
class UserAdmin(RecipesCountMixin, DjangoUserAdmin):
    """Регистрация кастомной модели User."""

    related_name = 'recipes'
    readonly_fields = ('avatar_preview',)

    list_display = (
        'id',
        'username',
        'get_full_name',
        'email',
        'get_avatar',
        *RecipesCountMixin.list_display,
        'get_subscriptions_count',
        'get_followers_count',
    )

    list_filter = (
        'is_staff',
        'is_superuser',
        'is_active',
        HasRecipesFilter,
        HasSubscriptionsFilter,
        HasFollowersFilter,
    )

    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name',
    )

    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Персональная информация', {
            'fields': (
                'first_name',
                'last_name',
                'email',
                'avatar',
                'avatar_preview',
            )
        }),
        ('Права доступа', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
            )
        }),
        ('Важные даты', {
            'fields': ('last_login', 'date_joined')
        }),
    )

    @admin.display(description='ФИО')
    def get_full_name(self, account):
        return f'{account.first_name} {account.last_name}'.strip()

    @admin.display(description='Аватар')
    def get_avatar(self, obj):
        return render_image(obj, 'avatar')

    @admin.display(description='Аватар')
    def avatar_preview(self, obj):
        return render_image(obj, 'avatar')

    @admin.display(description='Подписки')
    def get_subscriptions_count(self, account):
        return account.subscriptions.count()

    @admin.display(description='Подписчики')
    def get_followers_count(self, account):
        return account.author_subscriptions.count()


@admin.register(Tag)
class TagAdmin(RecipesCountMixin, admin.ModelAdmin):
    """Регистрация модели Tag."""

    related_name = 'recipes'
    list_display = ('id', 'name', 'slug',
                    *RecipesCountMixin.list_display)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'slug')

    def _get_recipes_queryset(self, obj):
        return obj.recipes.all()


@admin.register(Ingredient)
class IngredientAdmin(RecipesCountMixin, admin.ModelAdmin):
    """Регистрация модели Ingredient."""

    related_name = 'recipe_ingredients'
    list_display = ('id', 'name', 'measurement_unit',
                    *RecipesCountMixin.list_display)
    list_filter = (
        'measurement_unit',
        UsedInRecipesFilter)
    search_fields = ('name', 'measurement_unit')

    def _get_recipes_queryset(self, obj):
        return Recipe.objects.filter(recipe_ingredients__ingredient=obj)


class RecipeIngredientInline(admin.TabularInline):
    """Вставка IngredientAmount."""

    model = RecipeIngredient
    extra = 1
    autocomplete_fields = ['ingredient']


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Регистрация модели Рецепт."""

    readonly_fields = ('created_at', 'image_preview')

    list_display = ('id', 'name', 'cooking_time_display', 'author',
                    'get_favorites_count', 'get_ingredients',
                    'get_tags', 'get_image')
    list_filter = ('tags', 'author', CookingTimeFilter)
    search_fields = ('name', 'author__username', 'tags__name',
                     'tags__slug', 'recipe_ingredients__ingredient__name',)
    inlines = [RecipeIngredientInline]
    filter_horizontal = ('tags',)
    fieldsets = (
        ('Основное', {
            'fields': ('name', 'author', 'text', 'image', 'image_preview')}),
        ('Детали', {
            'fields': ('cooking_time', 'tags')}),
        ('Даты', {
            'fields': ('created_at',),
            'classes': ('collapse',)}),
    )

    @admin.display(description='В избранном')
    def get_favorites_count(self, recipes):
        """Подсчет количества в избранном."""
        return recipes.favorites.count()

    @admin.display(description='Продукты')
    @mark_safe
    def get_ingredients(self, recipe):
        return '<br>'.join(
            f'{ri.ingredient.name} — {ri.amount} '
            f'{ri.ingredient.measurement_unit}'
            for ri in recipe.recipe_ingredients.all())

    @admin.display(description='Вид')
    def get_image(self, obj):
        return render_image(obj, 'image')

    @admin.display(description='Вид рецепта')
    def image_preview(self, obj):
        return render_image(obj, 'image')

    @admin.display(description='Теги')
    @mark_safe
    def get_tags(self, recipe):
        return '<br>'.join(
            tag.name for tag in recipe.tags.all())

    @admin.display(description=mark_safe('Время<br>(мин)'))
    def cooking_time_display(self, recipe):
        return recipe.cooking_time


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Регистрация сводной модели RecipeIngredient."""

    list_display = ('recipe', 'ingredient', 'amount')
    list_filter = ('recipe', 'ingredient')
    search_fields = ('recipe__title', 'ingredient__name')
    autocomplete_fields = ['recipe', 'ingredient']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Регистрация модели Подписки."""

    list_display = ('user', 'author')
    search_fields = ('follower__username', 'following__username')