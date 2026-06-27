import base64
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator
from djoser.serializers import (
    TokenCreateSerializer as BaseTokenCreateSerializer
)
from rest_framework import serializers

from favorites.models import Favorite
from recipes.models import (
    Ingredient, Recipe, RecipeIngredient, RecipeTag, Tag
)
from shopping_cart.models import ShoppingCart
from subscriptions.models import Subscription

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Поле для декодирования изображений из формата Base64."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr), name=f'temp.{ext}'
            )
        return super().to_internal_value(data)


class CustomUserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации нового пользователя."""
    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'password'
        )
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class CustomUserSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения информации о пользователе."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name',
            'last_name', 'avatar', 'is_subscribed'
        )
        read_only_fields = ('id',)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Subscription.objects.filter(
            user=request.user, author=obj
        ).exists()


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления или обновления аватара."""

    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class CustomTokenCreateSerializer(BaseTokenCreateSerializer):
    """Кастомный сериализатор для аутентификации по email."""

    password = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = User
        fields = ('email', 'password')

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        if not email or not password:
            raise serializers.ValidationError(
                'Поля email и password обязательны'
            )
        user = User.objects.filter(email=email).first()
        if not user or not user.check_password(password):
            raise serializers.ValidationError(
                'Невозможно войти с предоставленными данными.'
            )
        attrs['user'] = user
        return attrs


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с тегами рецептов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с ингредиентами."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeShortSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор рецепта для списков подписок и покупок."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для связи ингредиента и рецепта с количеством."""

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True
    )
    amount = serializers.IntegerField(validators=[MinValueValidator(1)])

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для детального отображения рецептов."""

    author = CustomUserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, read_only=True, source='recipe_ingredients'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Favorite.objects.filter(
            user=request.user, recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return ShoppingCart.objects.filter(
            user=request.user, recipe=obj
        ).exists()

class RecipeCreateIngredientSerializer(serializers.Serializer):
    """Вспомогательный сериализатор для создания ингредиентов в рецепте."""
    id = serializers.IntegerField()
    amount = serializers.IntegerField(validators=[MinValueValidator(1)])


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецептов."""

    ingredients = RecipeCreateIngredientSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        validators=[MinValueValidator(1)]
    )

    class Meta:
        model = Recipe
        fields = (
            'name', 'text', 'image', 'cooking_time', 'ingredients', 'tags'
        )

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'Должен быть выбран хотя бы один тег.'
            )
        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                'Теги не должны повторяться.'
            )
        return value

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Должен быть хотя бы один ингредиент.'
            )

        ingredients_list = []
        for item in value:
            # item — это словарь, например {'id': 1, 'amount': 10}
            ingredient_id = item.get('id')
            if ingredient_id in ingredients_list:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться.'
                )
            ingredients_list.append(ingredient_id)

            # Проверяем количество
            amount = item.get('amount')
            if int(amount) < 1:
                raise serializers.ValidationError(
                    'Количество ингредиента должно быть больше 0.'
                )

        return value

    def create_ingredients(self, recipe, ingredients_data):
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=d['id'],
                amount=d['amount']
            )
            for d in ingredients_data
        ])

    def create_tags(self, recipe, tags):
        RecipeTag.objects.bulk_create([
            RecipeTag(recipe=recipe, tag=tag) for tag in tags
        ])

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
        for attr, value in validated_data.items():
            setattr(recipe, attr, value)
        recipe.save()
        if ingredients_data is not None:
            recipe.recipe_ingredients.all().delete()
            self.create_ingredients(recipe, ingredients_data)
        if tags is not None:
            recipe.recipe_tags.all().delete()
            self.create_tags(recipe, tags)
        return recipe

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data


class SubscriptionSerializer(CustomUserSerializer):
    """Сериализатор для управления подписками на авторов."""

    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + ('recipes_count', 'recipes')

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit') if request else None
        recipes = obj.recipes.all()
        if limit:
            try:
                recipes = recipes[:int(limit)]
            except ValueError:
                pass
        return RecipeShortSerializer(
            recipes, many=True, context=self.context
        ).data
