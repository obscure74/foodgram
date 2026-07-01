from django.contrib import admin


class HasRelationFilter(admin.SimpleListFilter):
    """Базовый фильтр наличия связи."""

    LOOKUPS = (('yes', 'Да'),
               ('no', 'Нет'))

    related_name = ''

    def lookups(self, request, model_admin):
        return self.LOOKUPS

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'yes':
            return queryset.filter(
                **{f'{self.related_name}__isnull': False}
            ).distinct()
        if value == 'no':
            return queryset.filter(
                **{f'{self.related_name}__isnull': True})
        return queryset


class HasRecipesFilter(HasRelationFilter):
    title = 'Есть рецепты'
    parameter_name = 'has_recipes'
    related_name = 'recipes'


class HasSubscriptionsFilter(HasRelationFilter):
    title = 'Есть подписки'
    parameter_name = 'has_subscriptions'
    related_name = 'subscriptions'


class HasFollowersFilter(HasRelationFilter):
    title = 'Есть подписчики'
    parameter_name = 'has_followers'
    related_name = 'author_subscriptions'


class CookingTimeFilter(admin.SimpleListFilter):
    """Фильтр рецептов по времени приготовления."""

    title = 'Время приготовления'
    parameter_name = 'cooking_time_group'

    def lookups(self, request, model_admin):
        recipes = model_admin.model.objects

        times = recipes.values_list('cooking_time', flat=True).distinct()

        if times.count() < 3:
            self.time_ranges = {}
            return ()

        times = tuple(times.order_by('cooking_time'))

        fast_threshold = times[len(times) // 3]
        slow_threshold = times[(2 * len(times)) // 3]

        self.time_ranges = {
            'fast': (times[0], fast_threshold),
            'medium': (fast_threshold + 1, slow_threshold),
            'slow': (slow_threshold + 1, times[-1])}

        return (
            ('fast',
                f'Быстрые (до {fast_threshold} мин)'),
            ('medium',
                f'Средние ({fast_threshold + 1}–{slow_threshold} мин)'),
            ('slow',
                f'Долгие (от {slow_threshold} мин)'))

    def queryset(self, request, recipes):
        if self.value() not in self.time_ranges:
            return recipes

        return recipes.filter(
            cooking_time__range=self.time_ranges[self.value()])


class UsedInRecipesFilter(HasRelationFilter):
    title = 'Используется в рецептах'
    parameter_name = 'used_in_recipes'
    related_name = 'recipe_ingredients'