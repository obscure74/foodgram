from rest_framework import serializers

from recipes.models import Recipe


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор короткого рецепта."""

    class Meta:

        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields