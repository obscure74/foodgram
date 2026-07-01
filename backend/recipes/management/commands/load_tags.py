from recipes.management.commands.load_json_base import BaseLoadJSONCommand
from recipes.models import Tag


class Command(BaseLoadJSONCommand):
    """Загрузка тегов."""

    model = Tag
    file_name = 'tags.json'