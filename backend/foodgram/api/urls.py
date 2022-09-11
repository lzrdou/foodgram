from rest_framework.routers import SimpleRouter

from django.urls import include, path

from .views import TagViewSet, RecipeViewSet, IngredientViewSet, UserViewSet

app_name = "api"

router = SimpleRouter()

router.register('tags', TagViewSet, basename='tags')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register("users", UserViewSet)

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path("", include(router.urls)),
]
