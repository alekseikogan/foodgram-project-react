import base64

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core import exceptions
from django.contrib.auth.password_validation import validate_password
from djoser.serializers import UserCreateSerializer, UserSerializer
from backend.recipes.models import Subscribe
from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingСart, Tag)
from rest_framework import serializers
from rest_framework.relations import SlugRelatedField
from rest_framework.validators import UniqueTogetherValidator

# ┌----------------------------------------------------------------------┐
# |                         Приложение Users                             |
# └----------------------------------------------------------------------┘


class UserReadSerializer(UserSerializer):
    '''Вывод списка пользователей - метод GET'''
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        if self.context.get('request'):
            if not self.context['request'].user.is_anonymous:
                return Subscribe.objects.filter(
                    user=self.context['request'].user,
                    author=obj).exists()
        return False


class UserCreateSerializer(UserCreateSerializer):
    '''Создание нового пользователя - метод POST'''
    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name',
                  'password')
        extra_kwargs = {
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
            'email': {'required': True, 'allow_blank': False},
        }

    def validate(self, obj):
        '''Проверка недопустимых username'''
        invalid_usernames = ['me', 'set_password',
                             'subscriptions', 'subscribe']
        if self.initial_data.get('username') in invalid_usernames:
            raise serializers.ValidationError(
                {'username': 'Использование данного username недопустимо!'}
            )
        return obj


class SetPasswordSerializer(serializers.Serializer):
    '''Изменение пароля пользователя - метод POST'''
    current_password = serializers.CharField()
    new_password = serializers.CharField()

    def validate(self, obj):
        '''Проверка пароля'''
        try:
            validate_password(obj['new_password'])
        except exceptions.ValidationError as error:
            raise serializers.ValidationError(
                {'new_password': list(error.messages)}
            )
        return super().validate(obj)

    def update(self, instance, validated_data):
        '''Обновление пароля'''
        if not instance.check_password(validated_data['current_password']):
            raise serializers.ValidationError(
                {'current_password': 'Неправильный пароль!'}
            )
        if (validated_data['current_password']
           == validated_data['new_password']):
            raise serializers.ValidationError(
                {'new_password': 'Новый пароль совпадает со старым!'}
            )
        instance.set_password(validated_data['new_password'])
        instance.save()
        return validated_data


class SubscriptionsSerializer(serializers.ModelSerializer):
    """[GET] Список авторов на которых подписан пользователь."""
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id',
                  'username', 'first_name',
                  'last_name', 'is_subscribed',
                  'recipes', 'recipes_count')

    def get_is_subscribed(self, obj):
        return (
            self.context.get('request').user.is_authenticated
            and Subscribe.objects.filter(user=self.context['request'].user,
                                         author=obj).exists()
        )

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = RecipeSerializer(recipes, many=True, read_only=True)
        return serializer.data


class RecipeSerializer(serializers.ModelSerializer):
    '''Список рецептов для отображения в избранном.'''
    name = serializers.ReadOnlyField()
    image = Base64ImageField(read_only=True)
    cooktime = serializers.ReadOnlyField()

    class Meta:
        model = Recipe
        fields = ('id', 'name',
                  'image', 'cooktime')


class SubscribeAuthorSerializer(serializers.ModelSerializer):
    '''Оформление подписки/отписки на автора - методы POST, DELETE'''
    email = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()
    is_subscribed = serializers.SerializerMethodField()
    recipes = RecipeSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id',
                  'username', 'first_name',
                  'last_name', 'is_subscribed',
                  'recipes', 'recipes_count')

    def validate(self, obj):
        if (self.context['request'].user == obj):
            raise serializers.ValidationError(
                {'errors': 'Ошибка при подписке!'})
        return obj

    def get_is_subscribed(self, obj):
        return (
            self.context.get('request').user.is_authenticated
            and Subscribe.objects.filter(user=self.context['request'].user,
                                         author=obj).exists())

    def get_recipes_count(self, obj):
        return obj.recipes.count()


# ┌----------------------------------------------------------------------┐
# |                         Приложение Recipes                           |
# └----------------------------------------------------------------------┘
class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class IngredientSerializer(serializers.ModelSerializer):
    '''Список ингредиентов - метод GET.'''
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    '''Список тегов - метод GET.'''
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientRecipeSerializer(serializers.ModelSerializer):
    '''Список ингредиентов для промежуточной модели.'''
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measure = serializers.ReadOnlyField(
        source='ingredient.measure')

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name',
                  'measure', 'amount')


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


class IngredientRecipeCreateSerializer(serializers.ModelSerializer):
    '''Ингредиент и количество для создания рецепта.'''
    id = serializers.IntegerField()

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    '''Создание, изменение и удаление рецепта - методы POST, PATCH, DELETE'''
    id = serializers.ReadOnlyField()
    author = UserReadSerializer(read_only=True)
    image = Base64ImageField()
    ingredients = IngredientRecipeCreateSerializer(many=True)
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
