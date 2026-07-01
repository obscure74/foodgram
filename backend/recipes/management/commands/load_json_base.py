import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class BaseLoadJSONCommand(BaseCommand):
    """Базовый загрузчик JSON фикстур."""

    model = None
    file_name = None

    def get_file_path(self):
        return Path(settings.BASE_DIR).parent / 'backend/data' / self.file_name

    def handle(self, *args, **options):
        try:
            with open(
                self.get_file_path(),
                encoding='utf-8'
            ) as file:

                created = self.model.objects.bulk_create(
                    (
                        self.model(**item)
                        for item in json.load(file)
                    ),
                    ignore_conflicts=True)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Фикстура "{self.file_name}" загружена. '
                    f'Создано записей: {len(created)}'))
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f'Ошибка загрузки {self.file_name}: {e}'))