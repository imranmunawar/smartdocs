# Generated by Django 5.0.1 on 2024-05-11 22:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smartdocs_app', '0033_alter_template_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='template',
            name='access_level',
            field=models.CharField(choices=[('free', 'Free'), ('level-1', 'Level 1'), ('level-2', 'Level 2'), ('level-3', 'Level 3')], default='free', max_length=256),
        ),
    ]
