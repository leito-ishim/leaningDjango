# Generated by Django 5.0.3 on 2024-03-29 05:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0002_feedback'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='following',
            field=models.ManyToManyField(blank=True, related_name='followers', to='system.profile', verbose_name='Подписки'),
        ),
    ]