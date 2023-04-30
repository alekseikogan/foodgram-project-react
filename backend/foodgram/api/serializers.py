import base64

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core import exceptions
from django.contrib.auth.password_validation import validate_password
from djoser.serializers import UserCreateSerializer, UserSerializer
from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingСart, Tag)
from users.models import Subscribe
from rest_framework import serializers

# ┌----------------------------------------------------------------------┐
# |                         Приложение Users                             |
# └----------------------------------------------------------------------┘

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class UserReadSerializer(UserSerializer):
    '''Вывод списка пользователей - метод GET'''
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        if self.context.get('request'):
            if not self.context.get('request').user.is_anonymous:
                return Subscribe.objects.filter(
                    user=self.context.get('request').user,
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


# из приложения Recipe для SubscriptionsSerializer
class RecipeSerializer(serializers.ModelSerializer):
    '''Список рецептов для отображения в избранном'''
    name = serializers.ReadOnlyField()
    image = Base64ImageField(read_only=True)
    cooktime = serializers.ReadOnlyField()

    class Meta:
        model = Recipe
        fields = ('id', 'name',
                  'image', 'cooktime')


class SubscriptionsSerializer(serializers.ModelSerializer):
    '''Возвращает список авторов на которых подписан пользователь
    - метод GET'''
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_amount = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id',
                  'username', 'first_name',
                  'last_name', 'is_subscribed',
                  'recipes', 'recipes_amount')

    def get_is_subscribed(self, obj):
        return (
            self.context.get('request').user.is_authenticated
            and Subscribe.objects.filter(user=self.context.get('request').user,
                                         author=obj).exists())

    def get_recipes_amount(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = RecipeSerializer(recipes, many=True, read_only=True)
        return serializer.data


class SubscribeAuthorSerializer(serializers.ModelSerializer):
    '''Оформление подписки/отписки на автора - методы POST, DELETE'''
    email = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()
    is_subscribed = serializers.SerializerMethodField()
    recipes = RecipeSerializer(many=True, read_only=True)
    recipes_amount = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id',
                  'username', 'first_name',
                  'last_name', 'is_subscribed',
                  'recipes', 'recipes_amount')

    def validate(self, obj):
        if (self.context.get('request').user == obj):
            raise serializers.ValidationError(
                {'errors': 'Ошибка при подписке!'})
        return obj

    def get_is_subscribed(self, obj):
        return (
            self.context.get('request').user.is_authenticated
            and Subscribe.objects.filter(user=self.context.get('request').user,
                                         author=obj).exists())

    def get_recipes_amount(self, obj):
        return obj.recipes.count()


# ┌----------------------------------------------------------------------┐
# |                         Приложение Recipes                           |
# └----------------------------------------------------------------------┘


class IngredientSerializer(serializers.ModelSerializer):
    '''Список ингредиентов - метод GET'''
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    '''Список тегов - метод GET'''
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientRecipeSerializer(serializers.ModelSerializer):
    '''Список ингредиентов для промежуточной модели'''
    id = serializers.SerializerMethodField(
        method_name='get_id')
    name = serializers.SerializerMethodField(
        method_name='get_name')
    measurement_unit = serializers.SerializerMethodField(
        method_name='get_measurement_unit')

    def get_id(self, obj):
        return obj.ingredient.id

    def get_name(self, obj):
        return obj.ingredient.name

    def get_measurement_unit(self, obj):
        return obj.ingredient.measurement_unit

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    '''Получение списка рецептов - метод GET'''
    author = UserReadSerializer(read_only=True)
    image = Base64ImageField()
    tag = TagSerializer(
        many=True,
        read_only=True)
    ingredients = serializers.SerializerMethodField(
        method_name='get_ingredients'
    )
    is_favorited = serializers.SerializerMethodField(
        method_name='get_is_favorited'
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        method_name='get_is_in_shopping_car'
    )

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'name', 'image', 'description',
                  'ingredients', 'tag', 'cooktime', 'is_in_shopping_cart',
                  'is_favorited')

    def get_ingredients(self, obj):
        ingredients = IngredientRecipe.objects.filter(recipe=obj)
        serializer = IngredientRecipeSerializer(ingredients, many=True)

        return serializer.data

    def get_is_favorited(self, obj):
        '''Проверка рецепта на наличие в избранном'''
        return (
            self.context.get('request').user.is_authenticated
            and Favorite.objects.filter(
                user=self.context.get('request').user, recipe=obj).exists())

    def get_is_in_shopping_cart(self, obj):
        '''Проверка рецепта на наличие в списке покупок'''
        return (
            self.context.get('request').user.is_authenticated
            and ShoppingСart.objects.filter(
                user=self.context.get('request').user,
                recipe=obj).exists())


class IngredientRecipeCreateSerializer(serializers.ModelSerializer):
    '''Ингредиент и его количество для создания рецепта'''
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        # model = IngredientRecipe
        model = Ingredient
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    '''Создание, изменение и удаление рецепта - методы POST, PATCH, DELETE'''
    id = serializers.ReadOnlyField()
    author = UserReadSerializer(read_only=True)
    image = Base64ImageField()
    ingredients = IngredientRecipeCreateSerializer(many=True)
    tag = serializers.PrimaryKeyRelatedField(many=True,
                                             queryset=Tag.objects.all())
    cooktime = serializers.IntegerField()

    class Meta:
        model = Recipe
        exclude = ('pub_date',)

        # extra_kwargs = {
        #     'name': {'required': True, 'allow_blank': False},
        #     'image': {'required': True, 'allow_blank': False},
        #     'description': {'required': True, 'allow_blank': False},
        #     'ingredients': {'required': True, 'allow_blank': False},
        #     'tag': {'required': True, 'allow_blank': False},
        #     'cooktime': {'required': True},}

    def validate(self, obj):
        for field in ['name', 'text', 'cooking_time']:
            if not obj.get(field):
                raise serializers.ValidationError(
                    f'Поле "{field}" является обязательным для заполнения!')
        if not obj.get('tag'):
            raise serializers.ValidationError(
                'Пожалуйста укажите как минимум 1 тег!')
        if not obj.get('ingredients'):
            raise serializers.ValidationError(
                'Пожалуйста укажите как минимум 1 ингредиент!')
        '''Проверка уникальности ингредиентов'''
        inrgedients_all = [item['id'] for item in obj.get('ingredients')]
        ingredient_unicum = set(inrgedients_all)
        if len(ingredient_unicum) != len(inrgedients_all):
            raise serializers.ValidationError(
                'Не должно быть повтора индгредиентов!')