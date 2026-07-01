from django.http import Http404, HttpResponseRedirect

from recipes.models import Recipe


def short_link_redirect(request, recipe_id):
    if not Recipe.objects.filter(pk=recipe_id).exists():
        raise Http404('Рецепт не найден')
    return HttpResponseRedirect(f'/recipes/{recipe_id}/')