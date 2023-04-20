from django.contrib.auth import get_user_model
from django.db import models

from . import validators

User = get_user_model()


class Ingredient(models.Model):
    '''Ингредиенты'''
    name = models.CharField(
        max_length=150,
        unique=True,
        blank=False,
        verbose_name='Название')
    measure = models.CharField(
        max_length=15,
        verbose_name='Единица измерения')

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measure'],
                name='unique_ingredient')]

    def __str__(self):
        return f"Ингредиент '{self.name}'"


class Tag(models.Model):
    '''Теги'''
    name = models.CharField(
        max_length=255,
        verbose_name='Название')

    hexcolor = models.CharField(
        max_length=7,
        validators=[validators.HexColorValidator()],
        verbose_name='Код цвета')

    slug = models.SlugField(
        validators=[validators.TagSlugValidator()],
        unique=True,
        verbose_name='Слаг')

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return f'Тег {self.name}'


class Recipe(models.Model):
    '''Рецепты'''
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipe',
        blank=False,
        verbose_name='Автор')

    name = models.CharField(
        max_length=255,
        blank=False,
        verbose_name='Название')

    image = models.ImageField(
        upload_to='photos/%Y/%m/%d/',
        blank=False,
        verbose_name='Картинка')

    description = models.TextField(
        verbose_name='Описание',
        blank=False,
        help_text='Введите текст поста')

    ingredients = models.ManyToManyField(
        Ingredient,
        blank=False,
        verbose_name='Ингредиент',)

    tag = models.ManyToManyField(
        Tag,
        blank=False,
        verbose_name='Тег')

    cooktime = models.IntegerField(
        blank=False,
        validators=[
            validators.MinValueValidator(
                1,
                message='Время приготовления должно быть больше 1 минуты!'),
            validators.MaxValueValidator(
                1440,
                message='Время приготовления не может быть дольше 1 дня!')
        ],
        verbose_name='Время приготовления')

    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f"Рецепт '{self.name}'"


class IngredientRecipe(models.Model):
    '''Промежуточная модель Ингредиент-Рецепт'''
    recipe = models.ForeignKey(
        Recipe,
        related_name='ingredient_list',
        on_delete=models.CASCADE,
        verbose_name='Рецепт')
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент')
    amount = models.PositiveIntegerField(
        validators=[validators.MinValueValidator(
            1, message='Минимальное количество ингредиентов - 1!')
        ],
        verbose_name='Количество'
    )

    class Meta:
        verbose_name = 'Ингредиент (кол-во)'
        verbose_name_plural = 'Ингредиенты (кол-во)'
        ordering = ('ingredient__name',)
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingredient_in_recipe')]

    def __str__(self):
        return f'{self.ingredient.name} {self.amount} {self.ingredient.measurement_unit}'


class Favorite(models.Model):
    '''Избранные рецепты'''
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_recipes',
        verbose_name='Пользователь')

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт в избранном')

    class Meta:
        verbose_name = 'Избранные рецепты'
        verbose_name_plural = 'Избранные рецепты'
        ordering = ('user', 'recipe')
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite_recipe')]

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в избранное.'


class ShopList(models.Model):
    '''Список покупок'''
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shop_list',
        verbose_name='Пользователь')

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shop_list',
        verbose_name='Рецепт для покупки')

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        ordering = ('user', 'recipe')
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_recipe_in_shoplist')]

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в список покупок.'
