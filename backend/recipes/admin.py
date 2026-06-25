from django.contrib import admin

from .models import Ingredient, Recipe, RecipeIngredient, RecipeTag, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


class RecipeTagInline(admin.TabularInline):
    model = RecipeTag
    extra = 1


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'pub_date', 'favorites_count')
    search_fields = ('name', 'author__username')
    list_filter = ('tags',)
    inlines = [RecipeTagInline, RecipeIngredientInline]

    def favorites_count(self, obj):
        return obj.favorites.count()
    favorites_count.short_description = 'В избранном'
