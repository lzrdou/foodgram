from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from .filters import IngredientFilter
from .paginators import CustomPagination
from .permissions import RecipeAuthorOrAdminPermission
from .serializers import (IngredientSerializer, RecipeGetSerializer,
                          RecipePostSerializer, ShoppingFavoriteSerializer,
                          TagSerializer, UserSerializer,
                          UserSubscriptionSerializer)
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Follow, User


class UserViewSet(DjoserUserViewSet):
    """Вьюсет для пользователей."""
    pagination_class = CustomPagination

    @action(permission_classes=[IsAuthenticatedOrReadOnly],
            methods=['post', 'delete'],
            detail=True)
    def subscribe(self, request, id):
        """Метод подписки (отписки) на пользователя."""
        user = request.user
        if user.is_anonymous:
            return False
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
                serializer = UserSerializer(
                    author, context={'request': request}
                )
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
            return Response(
                {'error': 'Не удалось подписаться'},
                status=status.HTTP_400_BAD_REQUEST
            )
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
            return Response(
                {'error': 'Не удалось отписаться'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return None

    @action(permission_classes=[IsAuthenticated],
            methods=['get'],
            detail=False)
    def subscriptions(self, request):
        """Метод получения списка подписок."""
        user = request.user
        authors = User.objects.filter(following__user=user)
        page = self.paginate_queryset(authors)
        if page is not None:
            serializer = UserSubscriptionSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = UserSubscriptionSerializer(authors, many=True)
        return Response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет рецептов."""
    http_method_names = ['get', 'post', 'patch', 'delete']
    pagination_class = CustomPagination
    permission_classes = [
        IsAuthenticatedOrReadOnly,
        RecipeAuthorOrAdminPermission,
    ]
    filter_backends = (DjangoFilterBackend,)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(permission_classes=[IsAuthenticated],
            methods=['post', 'delete'],
            detail=True)
    def shopping_cart(self, request, pk):
        """Метод добавления рецепта в список покупок."""
        user = request.user
        recipe = Recipe.objects.get(id=pk)
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
                serializer = ShoppingFavoriteSerializer(
                    recipe, context={'request': request}
                )
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
        if request.method == 'DELETE':
            if not ShoppingCart.objects.filter(
                    user=user,
                    recipe=recipe,
            ).exists():
                return Response(
                    {'error': 'Вы не добавляли этот рецепт в корзину'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            shopping_cart_recipe = ShoppingCart.objects.get(
                user=user, recipe=recipe
            )
            if shopping_cart_recipe.delete():
                return Response(status=status.HTTP_204_NO_CONTENT)
        return None

    @action(permission_classes=[IsAuthenticated],
            methods=['get'],
            detail=False)
    def download_shopping_cart(self, request):
        """Метод загрузки списка покупок."""
        user = request.user
        shopping_cart_dict = {}
        cart_objects = ShoppingCart.objects.filter(user=user)
        recipes_id_list = [obj.recipe_id for obj in cart_objects]
        recipes_ingredients = RecipeIngredient.objects.filter(
            recipe_id__in=recipes_id_list
        )
        for obj in recipes_ingredients:
            name = obj.ingredient.name
            measurement_unit = obj.ingredient.measurement_unit
            amount = obj.amount
            if obj.ingredient.name not in shopping_cart_dict:
                shopping_cart_dict[name] = [measurement_unit, amount]
            else:
                shopping_cart_dict[name][1] += amount
        response = HttpResponse(content_type='text/txt')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        response.write('"Продуктовый помощник"\nБутырин Артемий - 2022\n\n')
        for name, values in shopping_cart_dict.items():
            response.write(f'{name} - {values[1]} ({values[0]})\n')
        return response

    @action(permission_classes=[IsAuthenticated],
            methods=['post', 'delete'],
            detail=True)
    def favorite(self, request, pk):
        """Метод добавления рецепта в избранное."""
        user = request.user
        recipe = Recipe.objects.get(id=pk)
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
                serializer = ShoppingFavoriteSerializer(
                    recipe, context={'request': request}
                )
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
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
        return None

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'retrieve':
            return RecipeGetSerializer
        return RecipePostSerializer

    def get_queryset(self):
        queryset = Recipe.objects.all()
        is_favorited = self.request.query_params.get('is_favorited')
        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart'
        )
        author = self.request.query_params.get('author')
        tags = self.request.query_params.getlist('tags')
        user_id = self.request.user.id
        criterion_tags = Q(tags__slug__in=tags)

        if author:
            queryset = queryset.filter(author_id=author)
        elif tags:
            queryset = queryset.filter(criterion_tags).distinct()
        if user_id is not None:
            in_cart_list = [
                obj.recipe_id for obj in ShoppingCart.objects.filter(
                    user__id=user_id
                )
            ]
            favorite_set = [
                obj.recipe_id for obj in Favorite.objects.filter(
                    user__id=user_id
                )
            ]
            criterion_fav = Q(id__in=favorite_set)
            criterion_cart = Q(id__in=in_cart_list)
            if is_favorited:
                if int(is_favorited) == 1:
                    queryset = queryset.filter(
                        criterion_fav & criterion_tags
                    ).distinct()
                elif int(is_favorited) == 0:
                    queryset = queryset.exclude(criterion_fav)
            elif is_in_shopping_cart:
                if int(is_in_shopping_cart) == 1:
                    queryset = queryset.filter(criterion_cart).distinct()
                if int(is_in_shopping_cart) == 0:
                    queryset = queryset.exclude(criterion_cart)
        return queryset
