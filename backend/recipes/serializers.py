import base64

from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator
from rest_framework import serializers

from users.serializers import CustomUserSerializer
from .models import Ingredient, Recipe, RecipeIngredient, RecipeTag, Tag


class Base64ImageField(serializers.ImageField):
    """Кастомное поле для обработки base64 изображений."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f'temp.{ext}')
        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецепте."""
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )
    amount = serializers.IntegerField(
        validators=[MinValueValidator(1, message='Минимум 1 единица')]
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения рецептов."""
    author = CustomUserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True,
        read_only=True,
        source='recipe_ingredients'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.favorites.filter(user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.shopping_cart.filter(user=request.user).exists()


class RecipeCreateIngredientSerializer(serializers.Serializer):
    """Сериализатор для создания ингредиентов в рецепте."""
    id = serializers.IntegerField()
    amount = serializers.IntegerField(
        validators=[MinValueValidator(1, message='Минимум 1 единица')]
    )


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления рецептов."""
    ingredients = RecipeCreateIngredientSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        validators=[MinValueValidator(1, message='Минимум 1 минута')]
    )

    class Meta:
        model = Recipe
        fields = (
            'name', 'text', 'image', 'cooking_time',
            'ingredients', 'tags'
        )

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Рецепт должен содержать хотя бы один ингредиент'
            )
        ingredient_ids = [item['id'] for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться'
            )
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'Рецепт должен содержать хотя бы один тег'
            )
        return value

    def create_ingredients(self, recipe, ingredients_data):
        recipe_ingredients = []
        for ingredient_data in ingredients_data:
            recipe_ingredients.append(
                RecipeIngredient(
                    recipe=recipe,
                    ingredient_id=ingredient_data['id'],
                    amount=ingredient_data['amount']
                )
            )
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create_tags(self, recipe, tags):
        recipe_tags = []
        for tag in tags:
            recipe_tags.append(RecipeTag(recipe=recipe, tag=tag))
        RecipeTag.objects.bulk_create(recipe_tags)

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        recipe = Recipe.objects.create(**validated_data)

        self.create_ingredients(recipe, ingredients_data)
        self.create_tags(recipe, tags)

        return recipe

    def update(self, recipe, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)

        # Обновляем основные поля
        for attr, value in validated_data.items():
            setattr(recipe, attr, value)
        recipe.save()

        # Обновляем ингредиенты
        if ingredients_data is not None:
            recipe.recipe_ingredients.all().delete()
            self.create_ingredients(recipe, ingredients_data)

        # Обновляем теги
        if tags is not None:
            recipe.recipe_tags.all().delete()
            self.create_tags(recipe, tags)

        return recipe

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data
