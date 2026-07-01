from collections import defaultdict
from datetime import datetime

MONTHS = {
    1: 'января',
    2: 'февраля',
    3: 'марта',
    4: 'апреля',
    5: 'мая',
    6: 'июня',
    7: 'июля',
    8: 'августа',
    9: 'сентября',
    10: 'октября',
    11: 'ноября',
    12: 'декабря',
}


def generate_shopping_list(user, ingredients_qs):
    """Формирование списка покупок."""
    today = datetime.now()
    date = f'{today.day:02d} {MONTHS[today.month]} {today.year}'
    ingredients = defaultdict(lambda: {'amount': 0})
    recipes = set()
    for item in ingredients_qs:
        name = item['ingredient__name'].capitalize()
        unit = item['ingredient__measurement_unit']

        ingredients[(name, unit)]['amount'] += item['amount']

        recipes.add(
            f'{item["recipe__name"]} '
            f'({item["recipe__author__username"]})')

    product_lines = [
        f'{i}. {name} ({unit}) - {data["amount"]}'
        for i, ((name, unit), data) in enumerate(
            ingredients.items(),
            start=1)]

    return '\n'.join([
        f'Список покупок от {date}',
        '',
        'Продукты:',
        *product_lines,
        '',
        'Рецепты:',
        *sorted(recipes),
    ])