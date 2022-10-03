import base64

from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.db import transaction
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from djoser.serializers import UserSerializer as BaseUserSerializer
from rest_framework import serializers

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            RecipeTag, ShoppingCart, Tag)
from users.models import Follow, User


class UserSerializer(BaseUserSerializer):
    """Общий сериализатор модели User."""
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(
            user=user,
            author=obj
        ).exists()


class UserCreateSerializer(BaseUserCreateSerializer):
    """Сериализатор для создания пользователя."""
    class Meta:
        model = User
        fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        )

    def to_representation(self, instance):
        serializer = UserCreateResponseSerializer(instance)
        return serializer.data


class UserCreateResponseSerializer(UserSerializer):
    """Сериализатор для ответа при создании пользователя."""
    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
        )


class UserSubscriptionSerializer(UserSerializer):
    """Сериализатор для отображения пользователей в подписках."""
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit is not None:
            try:
                limit = int(recipes_limit)
            except (TypeError, ValueError):
                raise serializers.ValidationError(
                    'Ошибка в формате recipes_limit'
                )
            recipes = Recipe.objects.filter(author=obj)[:limit]
        else:
            recipes = Recipe.objects.filter(author=obj)
        return ShoppingFavoriteSerializer(
            recipes, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор модели Ingredient."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        lookup_field = 'name'


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор модели Tag."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')
        lookup_field = 'id'


class CustomTagsField(serializers.Field):
    """Кастомное поле тега для сериализатора рецепта."""

    def to_representation(self, value):
        return TagSerializer(value, many=True).data

    def to_internal_value(self, data):
        for item in data:
            try:
                if isinstance(item, bool):
                    raise TypeError
                Tag.objects.get(pk=item)
            except ObjectDoesNotExist:
                raise serializers.ValidationError(
                    f'id of incorrect type={type(item).__name__}'
                )
        return data


class Base64ImageField(serializers.ImageField):
    """Метод кодирования и декодирования изображения."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class RecipeIngredientGetSerializer(serializers.ModelSerializer):
    """Сериализатор through модели RecipeIngredient (метод GET)."""

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeGetSerializer(serializers.ModelSerializer):
    """Сериализатор модели Recipe (метод GET)."""
    tags = CustomTagsField()
    author = UserSerializer(read_only=True,)
    ingredients = RecipeIngredientGetSerializer(
        many=True,
        source='recipe',
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart'
        )

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if not user.is_anonymous:
            return bool(Favorite.objects.filter(
                user=user,
                recipe=obj
            ).exists())
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if not user.is_anonymous:
            return bool(ShoppingCart.objects.filter(
                user=user,
                recipe=obj
            ).exists())
        return False


class RecipeIngredientPostSerializer(serializers.ModelSerializer):
    """Сериализатор through модели RecipeIngredient (метод POST)."""
    id = serializers.IntegerField(source='ingredient_id')
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipePostSerializer(serializers.ModelSerializer):
    """Сериализатор модели Recipe (метод POST)."""
    tags = CustomTagsField()
    image = Base64ImageField()
    ingredients = RecipeIngredientPostSerializer(
        many=True, source='ingredient'
    )

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    @transaction.atomic()
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredient')
        recipe = Recipe.objects.create(**validated_data)
        for tag in tags:
            current_tag = Tag.objects.get(id=tag)
            if RecipeTag.objects.filter(
                    recipe=recipe, tag=current_tag
            ).exists():
                raise serializers.ValidationError('Данный тэг уже добавлен!')
            RecipeTag.objects.create(recipe=recipe, tag=current_tag)
        for ingredient in ingredients:
            ingr_id = int(dict(ingredient)['ingredient_id'])
            amount = int(dict(ingredient)['amount'])
            ingredient_check = Ingredient.objects.get(id=ingr_id)
            if RecipeIngredient.objects.filter(
                    recipe=recipe, ingredient=ingredient_check
            ).exists():
                raise serializers.ValidationError(
                    'Данный ингредиент уже добавлен!'
                )
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient_check,
                amount=amount
            )
        return recipe

    @transaction.atomic()
    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        ingredients = validated_data.pop('ingredient')
        tags = validated_data.pop('tags')
        instance.tags.set(tags)
        instance.ingredients.clear()
        for ingredient in ingredients:
            ingr_id = int(dict(ingredient)['ingredient_id'])
            amount = int(dict(ingredient)['amount'])
            ingredient_check = Ingredient.objects.get(id=ingr_id)
            if RecipeIngredient.objects.filter(
                    recipe=instance, ingredient=ingredient_check).exists():
                raise serializers.ValidationError(
                    'Данный ингредиент уже добавлен!'
                )
            RecipeIngredient.objects.create(
                recipe=instance,
                ingredient=ingredient_check,
                amount=amount
            )
        instance.save()
        return instance

    def to_representation(self, instance):
        serializer = RecipeGetSerializer(instance, context=self.context)
        return serializer.data


class ShoppingFavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор модели Recipe для корзины и избранного."""
    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )