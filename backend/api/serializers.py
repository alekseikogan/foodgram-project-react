import base64

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions
from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator
from django.db import transaction
from djoser.serializers import UserCreateSerializer, UserSerializer
from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingСart, Tag)
from rest_framework import serializers
from users.models import Subscribe

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
        request = self.context.get('request')
        if request:
            if not request.user.is_anonymous:
                return Subscribe.objects.filter(
                    user=request.user,
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

    def validate_username(self, value):
        '''Проверка недопустимых username'''
        invalid_usernames = ['me', 'set_password',
                             'subscriptions', 'subscribe']
        if value.lower() in invalid_usernames:
            raise serializers.ValidationError(
                {'username': 'Использование данного username недопустимо!'}
            )
        return value


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
    cooking_time = serializers.ReadOnlyField()

    class Meta:
        model = Recipe
        fields = ('id', 'name',
                  'image', 'cooking_time')


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
        request = self.context.get('request')
        return (
            request.user.is_authenticated
            and Subscribe.objects.filter(user=request.user,
                                         author=obj).exists())

    def get_recipes_amount(self, obj):
        return obj.recipe.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipe.all()
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeSerializer(recipes, many=True).data


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
        request = self.context.get('request')
        return (
            request.user.is_authenticated
            and Subscribe.objects.filter(user=request.user,
                                         author=obj).exists())

    def get_recipes_amount(self, obj):
        return obj.recipe.count()


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
    id = serializers.ReadOnlyField(
        source='ingredient.id')
    name = serializers.ReadOnlyField(
        source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    '''Получение списка рецептов - метод GET'''
    author = UserReadSerializer(read_only=True)
    image = Base64ImageField()
    tags = TagSerializer(
        many=True,
        read_only=True)
    ingredients = serializers.SerializerMethodField(
        method_name='get_ingredients'
    )
    is_favorited = serializers.SerializerMethodField(
        method_name='get_is_favorited'
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        method_name='get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'name', 'image', 'text',
                  'ingredients', 'tags', 'cooking_time', 'is_in_shopping_cart',
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
    amount = serializers.IntegerField(
        validators=(
            MinValueValidator(
                1,
                message='Количество ингредиента должно быть 1 мин или более!'
            ),
        )
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')

    def validate_amount(value):
        '''Валидация количества ингредиента'''
        if value <= 0:
            raise serializers.ValidationError(
                'Количество ингредиента не может быть меньше нуля!'
            )
        return value


class RecipeCreateSerializer(serializers.ModelSerializer):
    '''Создание, изменение и удаление рецепта - методы POST, PATCH, DELETE'''
    id = serializers.ReadOnlyField()
    author = UserReadSerializer(read_only=True)
    image = Base64ImageField()
    ingredients = IngredientRecipeCreateSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(many=True,
                                              queryset=Tag.objects.all())
    cooking_time = serializers.IntegerField(
        validators=(
            MinValueValidator(
                1,
                message='Время приготовления не может быть отрицательным!'
            ),
        )
    )

    class Meta:
        model = Recipe
        exclude = ('pub_date',)

    def validate(self, obj):
        for field in ['name', 'text', 'cooking_time']:
            if not obj.get(field):
                raise serializers.ValidationError(
                    f'Поле "{field}" является обязательным для заполнения!')
        if not obj.get('tags'):
            raise serializers.ValidationError(
                'Пожалуйста укажите как минимум 1 тег!')
        # if not obj.get('ingredients'):
        #     raise serializers.ValidationError(
        #         'Пожалуйста укажите как минимум 1 ингредиент!')
        # '''Проверка уникальности ингредиентов'''
        # inrgedients_all = [item['id'] for item in obj.get('ingredients')]
        # ingredient_unicum = set(inrgedients_all)
        # if len(ingredient_unicum) != len(inrgedients_all):
        #     raise serializers.ValidationError(
        #         'Не должно быть повтора индгредиентов!')
        return obj
    
    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                'Необходимо выбрать ингредиенты!'
            )
        for ingredient in ingredients:
            if int(ingredient['amount']) <= 0:
                raise serializers.ValidationError(
                    'Количество ингредиента должно быть больше нуля!'
                )
        ids = [item['id'] for item in ingredients]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                'Ингредиенты в рецепте должны быть уникальными!'
            )
        return ingredients

    def validate_cooking_time(value):
        '''Валидация времени приготовления'''
        if value <= 0:
            raise serializers.ValidationError(
                'Время приготовления не может быть отрицательным!'
            )
        return value

    @transaction.atomic
    def tags_and_ingredients_set(self, recipe, tags, ingredients):
        recipe.tags.set(tags)
        IngredientRecipe.objects.bulk_create(
            [IngredientRecipe(
                recipe=recipe,
                ingredient=Ingredient.objects.get(pk=ingredient['id']),
                amount=ingredient['amount']
            ) for ingredient in ingredients]
        )

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop('author')
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=self.context['request'].user,
                                       **validated_data)
        self.tags_and_ingredients_set(recipe, tags, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time)
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        IngredientRecipe.objects.filter(
            recipe=instance,
            ingredient__in=instance.ingredients.all()).delete()
        self.tags_and_ingredients_set(instance, tags, ingredients)
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(instance,
                                    context=self.context).data
