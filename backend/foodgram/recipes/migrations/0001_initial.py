import django.core.validators
import django.db.models.deletion
import recipes.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Favorite',
            fields=[
                ('id', models.BigAutoField(auto_created=True,
                                           primary_key=True, serialize=False,
                                           verbose_name='ID')),
            ],
            options={
                'verbose_name': 'Избранные рецепты',
                'verbose_name_plural': 'Избранные рецепты',
                'ordering': ('user', 'recipe'),
            },
        ),
        migrations.CreateModel(
            name='Ingredient',
            fields=[
                ('id', models.BigAutoField(auto_created=True,
                                           primary_key=True, serialize=False,
                                           verbose_name='ID')),
                ('name', models.CharField(max_length=150, unique=True,
                                          verbose_name='Название')),
                ('measurement_unit', models.CharField(
                    max_length=15,
                    verbose_name='Единица измерения')),
            ],
            options={
                'verbose_name': 'Ингредиент',
                'verbose_name_plural': 'Ингредиенты',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='IngredientRecipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True,
                                           primary_key=True, serialize=False,
                                           verbose_name='ID')),
                ('amount', models.PositiveIntegerField(
                    validators=[
                        django.core.validators.MinValueValidator(
                            1,
                            message='Минимальное количество ингредиентов' +
                            ' - 1!')], verbose_name='Количество')),
            ],
            options={
                'verbose_name': 'Ингредиент (кол-во)',
                'verbose_name_plural': 'Ингредиенты (кол-во)',
                'ordering': ('ingredient__name',),
            },
        ),
        migrations.CreateModel(
            name='Recipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True,
                                           primary_key=True, serialize=False,
                                           verbose_name='ID')),
                ('name', models.CharField(max_length=255,
                                          verbose_name='Название')),
                ('image', models.ImageField(upload_to='photos/%Y/%m/%d/',
                                            verbose_name='Картинка')),
                ('description', models.TextField(
                    help_text='Введите текстописания',
                    verbose_name='Описание')),
                ('cooking_time',
                 models.IntegerField(
                    validators=[django.core.validators.MinValueValidator(
                        1,
                        message='Время приготовления должно быть больше ' +
                        '1 минуты!'),
                        django.core.validators.MaxValueValidator(
                            1440,
                            message='Время приготовления не может быть ' +
                            'дольше 1 дня!')],
                    verbose_name='Время приготовления')),
                ('pub_date', models.DateTimeField(
                    auto_now_add=True,
                    verbose_name='Дата публикации')),
            ],
            options={
                'verbose_name': 'Рецепт',
                'verbose_name_plural': 'Рецепты',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True,
                                           primary_key=True,
                                           serialize=False,
                                           verbose_name='ID')),
                ('name', models.CharField(max_length=255,
                                          verbose_name='Название')),
                ('color', models.CharField(
                    max_length=7,
                    validators=[recipes.validators.HexColorValidator()],
                    verbose_name='Код цвета')),
                ('slug', models.SlugField(
                    unique=True,
                    validators=[recipes.validators.TagSlugValidator()],
                    verbose_name='Слаг')),
            ],
            options={
                'verbose_name': 'Тег',
                'verbose_name_plural': 'Теги',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='ShoppingСart',
            fields=[
                ('id', models.BigAutoField(auto_created=True,
                                           primary_key=True,
                                           serialize=False,
                                           verbose_name='ID')),
                ('recipe', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='shopping_recipe',
                    to='recipes.recipe',
                    verbose_name='Рецепт для покупки')),
            ],
            options={
                'verbose_name': 'Список покупок',
                'verbose_name_plural': 'Список покупок',
                'ordering': ('user', 'recipe'),
            },
        ),
    ]
