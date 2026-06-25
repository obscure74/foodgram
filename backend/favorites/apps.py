"""
Модуль приложения favorites.

Приложение отвечает за функционал добавления рецептов в избранное.
Позволяет пользователям сохранять понравившиеся рецепты
в личный список избранного.
"""

from django.apps import AppConfig


class FavoritesConfig(AppConfig):
    """Конфигурация приложения favorites."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "favorites"
    verbose_name = "Избранное"
