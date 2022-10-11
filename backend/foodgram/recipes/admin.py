from django.contrib import admin
from django.forms.models import BaseInlineFormSet

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag, RecipeTag)


class RecipeIngredientInLineFormset(BaseInlineFormSet):
    def clean_ingredients(self):
        if len(self.cleaned_data['ingredients']) < 1:
            return 'Необходим минимум 1 ингредиент.'
        return self.cleaned_data['ingredients']


class RecipeIngredientsInline(admin.TabularInline):
    model = RecipeIngredient
    formset = RecipeIngredientInLineFormset
    min_num = 1
    extra = 0


class RecipeTagInLineFormset(BaseInlineFormSet):
    def clean_tags(self):
        if len(self.cleaned_data['tgs']) < 1:
            return 'Необходим минимум 1 тег.'
        return self.cleaned_data['tags']


class RecipeTagsInline(admin.TabularInline):
    model = RecipeTag
    formset = RecipeTagInLineFormset
    min_num = 1
    extra = 0


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
    search_fields = (
        'author',
        'name',
        'tags'
    )
    inlines = (RecipeIngredientsInline, RecipeTagsInline)
    empty_value_field = "-пусто-"

    def favorite_count(self, obj):
        return Favorite.objects.filter(recipe=obj).count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit'
    )
    list_filter = (
        'name',
    )
    search_fields = (
        'name',
    )
    empty_value_field = '-пусто-'


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
    search_fields = (
        'name',
    )
    empty_value_field = "-пусто-"


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = (
        'recipe',
        'ingredient',
        'amount'
    )
    list_filter = ('recipe', 'ingredient')
    search_fields = ('recipe', 'ingredient')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_filter = ('user', 'recipe')
    search_fields = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_filter = ('user', 'recipe')
    search_fields = ('user', 'recipe')
