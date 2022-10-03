# Generated by Django 4.1.1 on 2022-09-13 09:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0003_rename_priority_tag_color'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ingredient',
            name='amount',
        ),
        migrations.AddField(
            model_name='recipeingredient',
            name='amount',
            field=models.PositiveIntegerField(default=0),
        ),
    ]