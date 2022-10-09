from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .services import download_shopping_cart
from .views import IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet

app_name = 'api'

router = SimpleRouter()

router.register('tags', TagViewSet, basename='tags')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('users', UserViewSet)

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('recipes/download_shopping_cart/', download_shopping_cart),
    path('', include(router.urls)),
]
