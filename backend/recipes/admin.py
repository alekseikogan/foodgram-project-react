from django.contrib import admin

from .models import (Favorite, Ingredient, IngredientRecipe, Recipe, ShopList,
                     Tag)


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measure')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'measure')


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    list_display_links = ('id', 'user')
    search_fields = ('user', 'recipe')


class IngredientRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    list_display_links = ('id', 'recipe', 'ingredient')


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'tag', 'cooktime', 'pub_date')
    list_display_links = ('id', 'name', 'author')
    search_fields = ('name', 'tag')
    prepopulated_fields = {'slug': ('name',)}


class ShopListAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    list_display_links = ('id', 'user')
    search_fields = ('user', 'recipe')


class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'hexcolor')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'hexcolor')


admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(IngredientRecipe, IngredientRecipeAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(ShopList, ShopListAdmin)
admin.site.register(Tag, TagAdmin)
