from django.contrib import admin

from .models import (
    Favorite, Ingredient, IngredientRecipe, Recipe, ShoppingСart, Tag)


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measure',)
    search_fields = ('^name',)


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe',)
    list_display_links = ('id', 'user',)
    search_fields = ('user', 'recipe',)


class IngredientRecipeAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')

# добавил, тк ругалась на module 'django.contrib.admin' has no attribute 'display'
if not hasattr(admin, 'display'):
    def display(empty_value):
        def decorator(fn):
            fn.empty_value = empty_value
            return fn
        return decorator
    setattr(admin, 'display', display)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'favorite_amount',)
    search_fields = ('^name',)
    list_filter = ('author', 'name', 'tag',)

    @admin.display(empty_value='Не добавляли')
    def favorite_amount(self, obj):
        return Favorite.objects.filter(recipe=obj).count()

    favorite_amount.short_description = 'Сколько раз добавили в избранное'


class ShoppingСartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'hexcolor', 'slug',)


admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(IngredientRecipe, IngredientRecipeAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(ShoppingСart, ShoppingСartAdmin)
admin.site.register(Tag, TagAdmin)
