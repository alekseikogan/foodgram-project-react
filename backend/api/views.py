from datetime import date, datetime

from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingСart, Tag)
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from users.models import Subscribe, User

from .serializers import (IngredientSerializer, RecipeCreateSerializer,
                          RecipeReadSerializer, RecipeSerializer,
                          SetPasswordSerializer, SubscribeAuthorSerializer,
                          SubscriptionsSerializer, TagSerializer,
                          UserCreateSerializer, UserReadSerializer)
from .user_permissions import IsAuthorOrReadOnly


class UserViewSet(mixins.CreateModelMixin,
                  mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  viewsets.GenericViewSet):
    '''Вывод, создание пользователей, подписка, смена пароля'''
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = LimitOffsetPagination

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return UserReadSerializer
        return UserCreateSerializer

    @action(detail=False, methods=['get'],
            pagination_class=None,
            permission_classes=(IsAuthenticated,))
    def me(self, request):
        '''Профиль пользователя'''
        serializer = UserReadSerializer(request.user)
        return Response(serializer.data,
                        status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'],
            permission_classes=(IsAuthenticated,))
    def set_password(self, request):
        '''Изменение пароля'''
        serializer = SetPasswordSerializer(request.user, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response({'detail': 'Пароль успешно изменен!'},
                        status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=(IsAuthenticated,),
            pagination_class=LimitOffsetPagination)
    def subscriptions(self, request):
        '''Посмотреть подписки пользователя'''
        queryset = User.objects.filter(subscribing__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionsSerializer(page, many=True,
                                             context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, **kwargs):
        '''Подписаться на автора'''
        author = get_object_or_404(User, id=kwargs['pk'])

        if request.method == 'POST':
            serializer = SubscribeAuthorSerializer(
                author, data=request.data, context={"request": request})
            serializer.is_valid(raise_exception=True)
            Subscribe.objects.create(user=request.user, author=author)
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            get_object_or_404(Subscribe, user=request.user,
                              author=author).delete()
            return Response({'detail': 'Успешная отписка'},
                            status=status.HTTP_204_NO_CONTENT)


# ----------------------------------------------------------------------


class IngredientViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    '''Вывод одного или нескольких ингредиентов'''
    queryset = Ingredient.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class TagViewSet(mixins.ListModelMixin,
                 mixins.RetrieveModelMixin,
                 viewsets.GenericViewSet):
    '''Вывод одного или нескольких тегов'''
    queryset = Tag.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = TagSerializer
    pagination_class = None


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
        '''Формирование и скачивание файла с ингредиентами'''
        user = request.user
        current_date = date.today()
        current_date_time = datetime.now().time()
        if not user.shopping_cart.exists():
            return Response(
                {'detail': 'Ваш список покупок пуст!'},
                status=status.HTTP_400_BAD_REQUEST)

        ingredients = IngredientRecipe.objects.filter(
            recipe__shopping_cart__user=user
        ).values(
            'ingredient__name',
            'ingredient__measure'
        ).annotate(amount=Sum('amount'))

        items_to_buy = (
            f'Список продуктов для {user.get_full_name()}\n'
            f'Дата: {current_date.strftime("%m/%d/%Y")}'
            f'Время: {current_date_time.strftime("%H:%M:%S")}'
        )
        for ingredient in ingredients:
            items_to_buy += '\n'.join(
                f'- {ingredient["ingredient__name"]}'
                f'({ingredient["ingredient__measure"]})'
                f' - {ingredient["amount"]}')

        filename = f'{user.username}_items_to_buy.txt'
        response = HttpResponse(items_to_buy, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'

        return response
