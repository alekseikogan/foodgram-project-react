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

# Используйте подходящие типы related-полей; для некоторых данных вам потребуется использовать SerializerMethodField.


class RecipeSerializer(serializers.ModelSerializer):
    # author = SlugRelatedField(slug_field='username', read_only=True)
    # image = Base64ImageField(required=False, allow_null=True)
    # group = serializers.PrimaryKeyRelatedField(
    #     queryset=Group.objects.all(),
    #     required=False)

    class Meta:
        fields = '__all__'
        model = Recipe