from django.db.models import Sum
from django.http import HttpResponse
from rest_framework.decorators import api_view

from recipes.models import RecipeIngredient, ShoppingCart


@api_view(['GET'])
def download_shopping_cart(request):
    """Метод загрузки списка покупок."""
    user = request.user
    cart_objects = ShoppingCart.objects.filter(user=user)
    recipes_id_list = [obj.recipe_id for obj in cart_objects]
    ingredients = RecipeIngredient.objects.filter(
        recipe_id__in=recipes_id_list).values(
        'ingredient__name', 'ingredient__measurement_unit'
    ).annotate(
        amount=Sum('amount')
    ).order_by(
        'ingredient__name'
    )
    file = open('shopping-list.txt', 'a+')
    file.write('"Продуктовый помощник"\nБутырин Артемий - 2022\n\n')
    for ingredient in ingredients:
        name = ingredient['ingredient__name']
        amount = ingredient['amount']
        measurement_unit = ingredient['ingredient__measurement_unit']
        file.write(f'{name} - {amount} ({measurement_unit})\n')
    file.close()
    response = HttpResponse(content_type='text/txt')
    response.write(file)
    return response
