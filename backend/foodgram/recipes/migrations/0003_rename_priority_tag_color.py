# Generated by Django 4.1.1 on 2022-09-13 09:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0002_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='tag',
            old_name='priority',
            new_name='color',
        ),
    ]
