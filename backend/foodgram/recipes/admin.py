from django.contrib import admin

from .models import Favorite, Ingredient, Recipe, Tag


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'author',
        'favorite_count'
    )
    list_filter = (
        'author',
        'name',
        'tags'
    )
    empty_value_field = "-пусто-"

    def favorite_count(self):
        return Favorite.objects.filter(recipe=self).count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit'
    )
    list_filter = (
        'name',
    )
    empty_value_field = "-пусто-"


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'color',
        'slug'
    )
    list_filter = (
        'name',
    )
    empty_value_field = "-пусто-"
