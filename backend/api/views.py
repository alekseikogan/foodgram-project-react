from django.forms import ValidationError
from django.shortcuts import get_object_or_404
from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingСart, Tag)
from rest_framework import filters, permissions, viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated

from .serializers import RecipeSerializer
from .user_permissions import IsAuthorOrReadOnly


# Приложение Recipes
class RecipeViewSet(viewsets.ModelViewSet):
    '''Создает рецепт или возвращает список рецептов'''
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (
        IsAuthorOrReadOnly,
        permissions.IsAuthenticatedOrReadOnly,
    )
    pagination_class = LimitOffsetPagination

    def perform_create(self, serializer):
        '''Получение объекта - автор рецепта'''
        serializer.save(author=self.request.user)

# Для сохранения ингредиентов и тегов рецепта потребуется переопределить методы create и update в ModelSerializer
