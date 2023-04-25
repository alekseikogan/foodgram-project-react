from django.forms import ValidationError
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingСart, Tag)
from rest_framework import filters, permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse

from .serializers import (
    RecipeReadSerializer, RecipeCreateSerializer, RecipeSerializer
)
from .user_permissions import IsAuthorOrReadOnly


# Приложение Recipes
class RecipeViewSet(viewsets.ModelViewSet):
    '''Создает рецепт или возвращает список рецептов'''
    queryset = Recipe.objects.all()
    permission_classes = (
        IsAuthorOrReadOnly,
        permissions.IsAuthenticatedOrReadOnly,
    )
    filter_backends = (DjangoFilterBackend, )
    pagination_class = LimitOffsetPagination

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        '''Получение объекта - автор рецепта'''
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, **kwargs):
        '''Добавление или удаление рецепта из избранного'''
        recipe = get_object_or_404(Recipe, id=kwargs['pk'])
        if request.method == 'POST':
            serializer = RecipeSerializer(recipe, data=request.data,
                                          context={"request": request})
            serializer.is_valid(raise_exception=True)
            if not Favorite.objects.filter(user=request.user,
                                           recipe=recipe).exists():
                Favorite.objects.create(user=request.user, recipe=recipe)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response({
                'errors': 'Вы уже добавляли этот рецепт в избранное!'},
                status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            get_object_or_404(Favorite, user=request.user,
                              recipe=recipe).delete()
            return Response(
                {'detail': 'Вы успешно удалили рецепт из избранного!'},
                status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(IsAuthenticated,),
            pagination_class=None)
    def shopping_cart(self, request, **kwargs):
        '''Добавление или удаление рецепта из списока покупок'''
        recipe = get_object_or_404(Recipe, id=kwargs['pk'])

        if request.method == 'POST':
            serializer = RecipeSerializer(recipe, data=request.data,
                                          context={"request": request})
            serializer.is_valid(raise_exception=True)
            if not ShoppingСart.objects.filter(user=request.user,
                                               recipe=recipe).exists():
                ShoppingСart.objects.create(user=request.user, recipe=recipe)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response(
                {'errors': 'Вы уже добавляли этот рецепт в список покупок!'},
                status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            get_object_or_404(ShoppingСart, user=request.user,
                              recipe=recipe).delete()
            return Response(
                {'detail': 'Вы успешно удалили рецепт из списка покупок!'},
                status=status.HTTP_204_NO_CONTENT)

    @action(detail=False,
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        user = request.user
        if not user.shopping_cart.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        ingredients = IngredientRecipe.objects.filter(
            recipe__shopping_cart__user=user
        ).values(
            'ingredient__name',
            'ingredient__measure'
        ).annotate(amount=Sum('amount'))

        items_to_buy = (
            f'Купить продукты для: {user.get_full_name()}\n'
        )
        for ingredient in ingredients:
            items_to_buy += '\n'.join(
                f'- {ingredient["ingredient__name"]} '
                f'({ingredient["ingredient__measure"]})'
                f' - {ingredient["amount"]}')

        filename = f'{user.username}_items_to_buy.txt'
        response = HttpResponse(items_to_buy, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'

        return response
