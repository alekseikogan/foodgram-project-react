import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('recipes', '0005_rename_tag_recipe_tags'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shoppingсart',
            name='recipe',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='shopping_cart', to='recipes.recipe',
                verbose_name='Рецепт для покупки'),
        ),
        migrations.AlterField(
            model_name='shoppingсart',
            name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='shopping_cart', to=settings.AUTH_USER_MODEL,
                verbose_name='Пользователь'),
        ),
    ]
