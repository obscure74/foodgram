from rest_framework import serializers
from .models import ShoppingCart


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок."""
    
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=['user', 'recipe'],
                message='Рецепт уже в списке покупок'
            )
        ]

    def to_representation(self, instance):
        from recipes.serializers import RecipeSerializer
        return RecipeSerializer(
            instance.recipe,
            context=self.context
        ).data
