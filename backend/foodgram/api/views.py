import fpdf
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
# from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from recipes.models import (Ingredient, Tag, Recipe,
                              RecipeIngredient, Favorite, ShoppingCart)
from users.models import User, Follow

from .filters import IngredientFilter
from .permissions import AdminPermission, RecipeAuthorOrAdminPermission, AddedUserPermission
from .serializers import (IngredientSerializer,
                          UserSubscriptionSerializer,
                          TagSerializer, ShoppingFavoriteSerializer,
                          RecipeGetSerializer, RecipePostSerializer,
                          UserSerializer)
from .paginators import CustomPagination


class UserViewSet(DjoserUserViewSet):
    pagination_class = CustomPagination

    @action(permission_classes=[IsAuthenticated],
            methods=['post', 'delete'],
            detail=True)
    def subscribe(self, request, id):
        user = request.user
        author = get_object_or_404(User, id=id)
        if request.method == 'POST':
            if user == author:
                return Response(
                    {'error': 'Нельзя подписаться на себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if Follow.objects.filter(
                    user=user,
                    author=author,
            ).exists():
                return Response(
                    {'error': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if Follow.objects.create(user=user, author=author):
                serializer = UserSerializer(author, context={'request': request})
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            if not Follow.objects.filter(
                    user=user,
                    author=author,
            ).exists():
                return Response(
                    {'error': 'Вы не подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            follow = Follow.objects.get(user=user, author=author)
            if follow.delete():
                return Response(status=status.HTTP_204_NO_CONTENT)

    @action(permission_classes=[IsAuthenticated],
            methods=['GET'],
            detail=False)
    def subscriptions(self, request):
        user = request.user
        following = Follow.objects.filter(user=user)
        authors_id_list = [obj.author.id for obj in following]
        users = User.objects.filter(id__in=authors_id_list)
        serializer = UserSubscriptionSerializer(users, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticatedOrReadOnly, RecipeAuthorOrAdminPermission,]
    filter_backends = (DjangoFilterBackend,)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(permission_classes=[IsAuthenticated],
            methods=['post', 'delete'],
            detail=True)
    def shopping_cart(self, request, id):
        """Метод добавления рецепта в список покупок."""
        user = request.user
        recipe = Recipe.objects.get(id=id)
        if request.method == 'POST':
            if ShoppingCart.objects.filter(
                    user=user,
                    recipe=recipe,
            ).exists():
                return Response(
                    {'error': 'Вы уже добавили этот рецепт в корзину'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if ShoppingCart.objects.create(user=user, recipe=recipe):
                serializer = ShoppingFavoriteSerializer(recipe, context={'request': request})
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            if not ShoppingCart.objects.filter(
                    user=user,
                    recipe=recipe,
            ).exists():
                return Response(
                    {'error': 'Вы не добавляли этот рецепт в корзину'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            shopping_cart_recipe = ShoppingCart.objects.get(user=user, recipe=recipe)
            if shopping_cart_recipe.delete():
                return Response(status=status.HTTP_204_NO_CONTENT)

    @action(permission_classes=[IsAuthenticated],
            methods=['get'],
            detail=False)
    def download_shopping_cart(self, request):
        """Метод загрузки списка покупок."""
        user = request.user
        shopping_cart_dict = {}
        cart_objects = ShoppingCart.objects.all().filter(user=user)
        recipes_id_list = [recipe.id for recipe in cart_objects]
        recipes_ingredients = RecipeIngredient.objects.filter(recipe_id__in=recipes_id_list)
        for obj in recipes_ingredients:
            if obj.ingredient.name not in shopping_cart_dict:
                shopping_cart_dict[obj.ingredient.name]: [obj.ingredient.measurement_unit, obj.amount]
            else:
                shopping_cart_dict[obj.ingredient.name][1] += obj.amount
        pdf = fpdf.FPDF(format='A4')
        pdf.add_page()
        pdf.set_font("Arial", size=14)
        pdf.write(txt='Продуктовый помощник')
        pdf.ln()
        pdf.write('Бутырин Артемий, 2022')
        pdf.ln()
        for name, values in shopping_cart_dict.items():
            pdf.write(f'{name} - {values[1]} ({values[1]})')
            pdf.ln()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.pdf"'
        return response

    @action(permission_classes=[IsAuthenticated],
            methods=['post', 'delete'],
            detail=True)
    def favorite(self, request):
        """Метод добавления рецепта в избранное."""
        user = request.user
        recipe = Recipe.objects.get(id=id)
        if request.method == 'POST':
            if Favorite.objects.filter(
                    user=user,
                    recipe=recipe,
            ).exists():
                return Response(
                    {'error': 'Вы уже добавили этот рецепт в избранное'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if Favorite.objects.create(user=user, recipe=recipe):
                serializer = ShoppingFavoriteSerializer(recipe, context={'request': request})
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            if not Favorite.objects.filter(
                    user=user,
                    recipe=recipe,
            ).exists():
                return Response(
                    {'error': 'Вы не добавляли этот рецепт в избранное'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            favorite_recipe = Favorite.objects.get(user=user, recipe=recipe)
            if favorite_recipe.delete():
                return Response(status=status.HTTP_204_NO_CONTENT)

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'retrieve':
            return RecipeGetSerializer
        return RecipePostSerializer

    def get_queryset(self):
        queryset = Recipe.objects.all()
        is_favorited = self.request.query_params.get('is_favorited')
        is_in_shopping_cart = self.request.query_params.get('is_in_shopping_cart')
        author = self.request.query_params.get('author')
        tags = self.request.query_params.get('tags')

        if is_favorited:
            if int(is_favorited) == 1:
                queryset = queryset.filter(is_favorited=True)
            elif int(is_favorited) == 0:
                queryset = queryset.filter(is_favorited=False)
        elif is_in_shopping_cart:
            if int(is_in_shopping_cart) == 1:
                queryset = queryset.filter(is_in_shopping_cart=True)
            if int(is_in_shopping_cart) == 0:
                queryset = queryset.filter(is_in_shopping_cart=False)
        elif author:
            queryset = queryset.filter(author_id=author)
        elif tags:
            queryset = queryset.filter(tags__slug__in=tags)

        return queryset
