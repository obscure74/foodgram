import json

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Команда для загрузки ингредиентов из JSON файла."""

    help = 'Загрузка ингредиентов из JSON файла'

    def add_arguments(self, parser):
        """Добавляет аргумент командной строки."""
        parser.add_argument(
            'file_path',
            type=str,
            help='Путь к JSON файлу с ингредиентами'
        )

    def handle(self, *args, **options):
        """Основная логика команды."""
        file_path = options['file_path']

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            ingredients_to_create = []
            for item in data:
                ingredient = Ingredient(
                    name=item['name'],
                    measurement_unit=item['measurement_unit']
                )
                ingredients_to_create.append(ingredient)

            Ingredient.objects.bulk_create(ingredients_to_create)
            count = len(ingredients_to_create)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Успешно загружено {count} ингредиентов'
                )
            )
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(
                    f'Файл {file_path} не найден'
                )
            )
        except json.JSONDecodeError:
            self.stdout.write(
                self.style.ERROR(
                    f'Ошибка чтения JSON файла {file_path}'
                )
            )
