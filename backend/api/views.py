from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.filters import RecipeFilter
from api.pagination import CustomPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    CustomUserSerializer, CustomUserCreateSerializer, IngredientSerializer,
    RecipeCreateSerializer, RecipeSerializer, RecipeShortSerializer,
    SubscriptionSerializer, TagSerializer, AvatarSerializer
)
from djoser.serializers import SetPasswordSerializer
from favorites.models import Favorite
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from shopping_cart.models import ShoppingCart
from subscriptions.models import Subscription
from users.models import User


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для обработки запросов, связанных с пользователями."""

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [AllowAny]
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        return CustomUserSerializer

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def set_password(self, request):
        """Смена пароля текущего авторизованного пользователя."""
        serializer = SetPasswordSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        self.request.user.set_password(
            serializer.validated_data['new_password']
        )
        self.request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, pk=None):
        """Создание или удаление подписки на автора."""
        author = get_object_or_404(User, pk=pk)
        if request.user == author:
            return Response(
                {'errors': 'Нельзя подписаться на себя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.method == 'POST':
            subscription, created = Subscription.objects.get_or_create(
                user=request.user, author=author
            )
            if not created:
                return Response(
                    {'errors': 'Вы уже подписаны на этого автора'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            context = {'request': request}
            return Response(
                SubscriptionSerializer(author, context=context).data,
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            subscription = Subscription.objects.filter(
                user=request.user, author=author
            ).first()
            if not subscription:
                return Response(
                    {'errors': 'Подписка не найдена'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Получение списка авторов, на которых подписан пользователь."""
        subscribed_authors = User.objects.filter(
            subscribers__user=request.user
        ).order_by('id')

        page = self.paginate_queryset(subscribed_authors)
        if page is not None:
            serializer = SubscriptionSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionSerializer(
            subscribed_authors, many=True, context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['get', 'put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me'
    )
    def me(self, request):
        """Просмотр, редактирование или удаление своего профиля."""
        if request.method == 'GET':
            context = {'request': request}
            return Response(
                CustomUserSerializer(request.user, context=context).data
            )
        elif request.method == 'PUT':
            serializer = CustomUserSerializer(
                request.user,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == 'DELETE':
            request.user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated]
    )
    def avatar(self, request):
        """Установка или удаление аватара пользователя."""
        user = request.user
        if request.method == 'PUT':
            serializer = AvatarSerializer(
                user, data=request.data, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        if request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete()
                user.avatar = None
                user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для просмотра тегов (только чтение)."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для просмотра ингредиентов с поиском."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    pagination_class = None
    filter_backends = [filters.SearchFilter]
    search_fields = ["^name"]


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для управления рецептами."""

    queryset = Recipe.objects.all()
    permission_classes = [IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsAuthorOrReadOnly()]
        return [AllowAny()]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return RecipeCreateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Добавление рецепта в избранное или его удаление."""
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == "POST":
            favorite, created = Favorite.objects.get_or_create(
                user=request.user, recipe=recipe
            )
            if not created:
                return Response(
                    {"errors": "Рецепт уже в избранном"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                RecipeShortSerializer(recipe, context={"request": request}).data,
                status=status.HTTP_201_CREATED
            )
        elif request.method == "DELETE":
            favorite = get_object_or_404(
                Favorite, user=request.user, recipe=recipe
            )
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Добавление рецепта в список покупок или его удаление."""
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == "POST":
            cart_item, created = ShoppingCart.objects.get_or_create(
                user=request.user, recipe=recipe
            )
            if not created:
                return Response(
                    {"errors": "Рецепт уже в списке покупок"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            context = {"request": request}
            return Response(
                RecipeShortSerializer(recipe, context=context).data,
                status=status.HTTP_201_CREATED
            )
        elif request.method == "DELETE":
            cart_item = get_object_or_404(
                ShoppingCart, user=request.user, recipe=recipe
            )
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Формирование и выгрузка текстового файла со списком покупок."""
        shopping_recipes = ShoppingCart.objects.filter(
            user=request.user
        ).values_list("recipe_id", flat=True)
        if not shopping_recipes:
            return Response(
                {"errors": "Список покупок пуст"},
                status=status.HTTP_400_BAD_REQUEST
            )
        ingredients = (
            RecipeIngredient.objects
            .filter(recipe_id__in=shopping_recipes)
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total_amount=Sum("amount"))
            .order_by("ingredient__name")
        )
        content = []
        for item in ingredients:
            content.append(
                f"{item['ingredient__name']} "
                f"({item['ingredient__measurement_unit']}) — "
                f"{item['total_amount']}"
            )
        response = HttpResponse(
            "\n".join(content), content_type="text/plain; charset=utf-8"
        )
        response["Content-Disposition"] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[AllowAny],
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        """Получение короткой ссылки на рецепт."""
        recipe = get_object_or_404(Recipe, pk=pk)
        return Response({'short-link': f'/api/recipes/{recipe.id}/'})
