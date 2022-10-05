from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.utils.timezone import now

from users.models import User


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField(
        max_length=150,
        verbose_name='Название',
    )
    measurement_unit = models.CharField(
        max_length=60,
        verbose_name='Единицы измерения'
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Модель тега."""

    hex_validator = RegexValidator(
        regex=r'^[A-Fa-f0-9]{6}$',
        message=(
            'Неверный формат ввода (введите Hex код)'
        )
    )

    name = models.CharField(
        max_length=64,
        verbose_name='Название',
        unique=True
    )
    color = models.CharField(
        max_length=7,
        validators=[hex_validator, ],
        verbose_name='Цвет',
        default='#FF0000'
    )
    slug = models.SlugField(
        max_length=64,
        verbose_name='Slug',
        unique=True
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецепта."""

    name = models.CharField(
        max_length=200,
        verbose_name='Название'
    )
    pubdate = models.DateField(
        default=now,
        editable=False
    )
    image = models.ImageField(
        verbose_name='Изображение'
    )
    text = models.TextField(
        verbose_name='Текст'
    )
    cooking_time = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1, 'Минимальное значение: 1'),
        ],
        verbose_name='Время приготовления',
        help_text='Время приготовления в минутах'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        verbose_name='Тэги'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
    )

    class Meta:
        ordering = ['-pubdate']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        constraints = [
            models.UniqueConstraint(
                name='author_recipe_unique',
                fields=['author', 'name'],
            ),
        ]

    def __str__(self):
        return f'{self.name}'


class RecipeTag(models.Model):
    """Модель для связи рецепта и тега."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Тэг'
    )

    class Meta:
        verbose_name = 'Тег рецепта'
        verbose_name_plural = 'Теги рецептов'
        constraints = [
            models.UniqueConstraint(
                name='recipe_tag_unique',
                fields=['recipe', 'tag'],
            ),
        ]

    def __str__(self):
        return f'{self.recipe} {self.tag}'


class RecipeIngredient(models.Model):
    """Модель для связи рецепта и ингредиента."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1, 'Минимальное значение: 1'),
        ],
        verbose_name='Количество',
    )

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецептов'
        constraints = [
            models.UniqueConstraint(
                name='recipe_ingredient_unique',
                fields=['recipe', 'ingredient'],
            ),
        ]

    def __str__(self):
        return f'{self.recipe} {self.ingredient}'


class Favorite(models.Model):
    """Модель для добавления рецепта в избранное."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='fav_user',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='fav_recipe',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]


class ShoppingCart(models.Model):
    """Модель для добавления рецепта в список покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shop_user',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shop_recipe',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Рецепт в корзине'
        verbose_name_plural = 'Рецепты в корзине'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            )
        ]
