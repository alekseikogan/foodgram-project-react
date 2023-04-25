import base64

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingСart, Tag)
from rest_framework import serializers
from rest_framework.relations import SlugRelatedField
from rest_framework.validators import UniqueTogetherValidator


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class RecipeReadSerializer(serializers.ModelSerializer):
    '''Получение списка рецептов - метод GET'''
    author = UserReadSerializer(read_only=True)
    image = Base64ImageField()
    tag = TagSerializer(
        many=True,
        read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True,
        read_only=True,
        source='recipes')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'name', 'image', 'description',
                  'ingredients', 'tag', 'cooktime', 'is_in_shopping_cart',
                  'is_favorited')

    def get_is_favorited(self, obj):
        '''Проверка на наличие в избранном'''
        return (
            self.context.get('request').user.is_authenticated
            and Favorite.objects.filter(
                user=self.context['request'].user, recipe=obj).exists())

    def get_is_in_shopping_cart(self, obj):
        '''Проверка на наличие в списке покупок'''
        return (
            self.context.get('request').user.is_authenticated
            and ShoppingСart.objects.filter(
                user=self.context['request'].user,
                recipe=obj).exists())


class RecipeCreateSerializer(serializers.ModelSerializer):
    '''Создание, изменение и удаление рецепта - методы POST, PATCH, DELETE'''
    id = serializers.ReadOnlyField()
    author = UserReadSerializer(read_only=True)
    image = Base64ImageField()
    ingredients = RecipeIngredientCreateSerializer(many=True)
    tag = serializers.PrimaryKeyRelatedField(many=True,
                                             queryset=Tag.objects.all())

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'description',
                  'ingredients', 'tag', 'cooktime')
        extra_kwargs = {
            'name': {'required': True, 'allow_blank': False},
            'image': {'required': True, 'allow_blank': False},
            'description': {'required': True, 'allow_blank': False},
            'ingredients': {'required': True, 'allow_blank': False},
            'tag': {'required': True, 'allow_blank': False},
            'cooktime': {'required': True},}

    def validate(self, obj):
        for field in ['name', 'text', 'cooking_time']:
            if not obj.get(field):
                raise serializers.ValidationError(
                    f'Поле "{field}" является обязательным для заполнения!')
        if not obj.get('tag'):
            raise serializers.ValidationError(
                'Пожалуйста, укажите как минимум 1 тег!')
        if not obj.get('ingredients'):
            raise serializers.ValidationError(
                'Пожалуйста, укажите как минимум 1 ингредиент!')
        '''Проверка уникальности ингредиентов'''
        inrgedients_all = [item['id'] for item in obj.get('ingredients')]
        ingredient_unicum = set(inrgedients_all)
        if len(ingredient_unicum) != len(inrgedients_all):
            raise serializers.ValidationError(
                'Не должно быть повтора индгредиентов!')


class RecipeSerializer(serializers.ModelSerializer):
    """Список рецептов для отображения в избранном"""
    name = serializers.ReadOnlyField()
    image = Base64ImageField(read_only=True)
    cooktime = serializers.ReadOnlyField()

    class Meta:
        model = Recipe
        fields = ('id', 'name',
                  'image', 'cooktime')