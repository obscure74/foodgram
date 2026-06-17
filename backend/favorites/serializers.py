from rest_framework import serializers
from .models import Favorite


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для избранного."""
    
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=['user', 'recipe'],
                message='Рецепт уже в избранном'
            )
        ]

    def to_representation(self, instance):
        from recipes.serializers import RecipeSerializer
        return RecipeSerializer(
            instance.recipe,
            context=self.context
        ).data
