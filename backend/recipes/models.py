from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import MinValueValidator
from django.db import models

from recipes.constants import (MIN_AMOUNT_VALUE, MIN_TIME_COOK_VALUE,
                               SIZE_EMAIL_FIELD, SIZE_FIRSTNAME_FIELD,
                               SIZE_INGREDIENT_NAME_FIELD, SIZE_LASTNAME_FIELD,
                               SIZE_RECIPE_NAME_FIELD, SIZE_TAG_FIELDS,
                               SIZE_UNIT_FIELD, SIZE_USERNAME_FIELD)


class User(AbstractUser):
    """Кастомная модель пользователя."""

    email = models.EmailField(
        unique=True,
        verbose_name='Электронная почта',
        max_length=SIZE_EMAIL_FIELD)
    username = models.CharField(
        max_length=SIZE_USERNAME_FIELD,
        unique=True,
        validators=[UnicodeUsernameValidator()],
        verbose_name='Юзернейм')
    first_name = models.CharField(
        max_length=SIZE_FIRSTNAME_FIELD,
        verbose_name='Имя')
    last_name = models.CharField(
        max_length=SIZE_LASTNAME_FIELD,
        verbose_name='Фамилия')
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='Ссылка на аватар')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:

        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель Подписки."""

    user = models.ForeignKey(
        User,
        related_name='subscriptions',
        on_delete=models.CASCADE,
        verbose_name='Подписчик')

    author = models.ForeignKey(
        User,
        related_name='author_subscriptions',
        on_delete=models.CASCADE,
        verbose_name='Автор')

    class Meta:

        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'),

            models.CheckConstraint(
                condition=~models.Q(user=models.F('author')),
                name='prevent_self_subscription')]

    def __str__(self):
        return f'{self.user} подписан на {self.author}'


class Tag(models.Model):
    """Модель Теги."""

    name = models.CharField(
        max_length=SIZE_TAG_FIELDS,
        unique=True,
        verbose_name='Название')
    color = models.CharField(
        max_length=7,
        unique=True,
        verbose_name='Цвет')
    slug = models.SlugField(
        max_length=SIZE_TAG_FIELDS,
        unique=True,
        verbose_name='slug')

    class Meta:

        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель Продукты."""

    name = models.CharField(
        max_length=SIZE_INGREDIENT_NAME_FIELD,
        unique=True,
        verbose_name='Название продукта')
    measurement_unit = models.CharField(
        max_length=SIZE_UNIT_FIELD,
        verbose_name='Единица измерения')

    class Meta:

        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'

    @property
    def recipes(self):
        return Recipe.objects.filter(
            recipe_ingredients__ingredient=self)


class Recipe(models.Model):
    """Модель рецепта."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор')
    name = models.CharField(
        max_length=SIZE_RECIPE_NAME_FIELD,
        verbose_name='Название')
    text = models.TextField(
        verbose_name='Описание')
    cooking_time = models.PositiveSmallIntegerField(
        help_text='Время в минутах',
        validators=[MinValueValidator(MIN_TIME_COOK_VALUE)],
        verbose_name='Время приготовления (мин)')
    image = models.ImageField(
        upload_to='images/',
        verbose_name='Ссылка на картинку на сайте')
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания')
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='recipes',
        verbose_name='Теги')

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Связующая таблица: рецепт + продукт + количество."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт')
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Продукт')
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(MIN_AMOUNT_VALUE)],
        verbose_name='Количество')

    class Meta:
        verbose_name = 'Количество продукта'
        verbose_name_plural = 'Количество продуктов'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient')]

    def __str__(self):
        return (f'{self.recipe.name}: '
                f'{self.amount} '
                f'{self.ingredient.measurement_unit} '
                f'{self.ingredient.name}')


class UserRecipeBaseModel(models.Model):
    """Базовая модель."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь')
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт')

    class Meta:

        abstract = True
        default_related_name = '%(class)ss'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_%(class)s')]

    def __str__(self):
        return f'{self.user.username} → {self.recipe.name}'


class Favorite(UserRecipeBaseModel):
    """Модель Избранное."""

    class Meta(UserRecipeBaseModel.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(UserRecipeBaseModel):
    """Модель Список покупок."""

    class Meta(UserRecipeBaseModel.Meta):
        verbose_name = 'Для покупок'
        verbose_name_plural = 'Для покупок'
