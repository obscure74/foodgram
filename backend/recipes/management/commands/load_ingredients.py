import json
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузка ингредиентов из JSON файла'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Путь к JSON файлу с ингредиентами'
        )

    def handle(self, *args, **options):
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
            self.stdout.write(
                self.style.SUCCESS(f'Успешно загружено {len(ingredients_to_create)} ингредиентов')
            )
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'Файл {file_path} не найден')
            )
        except json.JSONDecodeError:
            self.stdout.write(
                self.style.ERROR(f'Ошибка чтения JSON файла {file_path}')
            )
