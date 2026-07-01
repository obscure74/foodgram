from drf_extra_fields.fields import Base64ImageField
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from api.serializers.users import UserSerializer
from recipes.constants import MIN_AMOUNT_VALUE, MIN_TIME_COOK_VALUE
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:

        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для продуктов."""

    class Meta:

        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    """Сериализатор для получения игредиентов в рецепте (GET)."""

    id = serializers.ReadOnlyField(
        source='ingredient.id')
    name = serializers.ReadOnlyField(
        source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:

        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = fields


class RecipeIngredientWriteSerializer(serializers.Serializer):
    """Сериализатор для записи игредиентов в рецепт (POST/PATCH)."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(
        min_value=MIN_AMOUNT_VALUE)


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для получения рецепта (GET)."""

    tags = TagSerializer(
        many=True,
        read_only=True)
    author = UserSerializer(
        read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        many=True,
        source='recipe_ingredients')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:

        model = Recipe
        fields = ('id', 'tags', 'name', 'text', 'ingredients', 'author',
                  'image', 'cooking_time', 'is_favorited',
                  'is_in_shopping_cart')
        read_only_fields = fields

    def _is_relation_exists(self, recipe, model):
        request = self.context.get('request')

        return (request
                and request.user.is_authenticated
                and model.objects.filter(
                    recipe=recipe,
                    user=request.user,
                ).exists())

    @extend_schema_field(serializers.BooleanField)
    def get_is_favorited(self, recipe):
        return self._is_relation_exists(recipe, Favorite)

    @extend_schema_field(serializers.BooleanField)
    def get_is_in_shopping_cart(self, recipe):
        return self._is_relation_exists(recipe, ShoppingCart)


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор создания и обновления рецептов."""

    image = Base64ImageField(required=True,
                             allow_null=False,
                             allow_empty_file=False)
    ingredients = RecipeIngredientWriteSerializer(
        many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True)
    author = serializers.HiddenField(
        default=serializers.CurrentUserDefault())
    cooking_time = serializers.IntegerField(
        min_value=MIN_TIME_COOK_VALUE)

    class Meta:

        model = Recipe
        fields = ('ingredients', 'tags', 'image', 'name',
                  'text', 'author', 'cooking_time')

    def create_ingredients(self, ingredients, recipe):
        """Метод для создания продуктов в рецепте."""
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['id'],
                amount=item['amount'])
            for item in ingredients)

    def create(self, validated_data):
        """Метод для создания рецепта."""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = super().create(validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, recipe, validated_data):
        """Метод для обновления рецепта."""
        recipe.tags.set(validated_data.pop('tags'))
        recipe.recipe_ingredients.all().delete()
        self.create_ingredients(
            validated_data.pop('ingredients'),
            recipe)
        return super().update(recipe, validated_data)

    def to_representation(self, instance):
        """Метод для представления рецепта."""
        return RecipeReadSerializer(
            instance,
            context=self.context).data

    def _validate_duplicates(self, records_id, field_name):
        duplicates = {
            record_id for record_id in records_id
            if records_id.count(record_id) > 1}
        if duplicates:
            raise serializers.ValidationError(
                f'Повторяются {field_name}: {duplicates}')

    def validate(self, data):
        """Общая валидация."""

        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                'Должен быть хотя бы один продукт')
        ingredient_ids = [
            ingredient['id']
            for ingredient in ingredients]
        self._validate_duplicates(ingredient_ids, 'продукты')

        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                'Должен быть хотя бы один тег')
        tag_ids = [tag.id for tag in tags]
        self._validate_duplicates(tag_ids, 'теги')
        return data