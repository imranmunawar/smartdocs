# Generated by Django 5.0.1 on 2024-04-29 19:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smartdocs_app', '0032_question_sequence_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='template',
            name='name',
            field=models.CharField(help_text='Name of the Template', max_length=300),
        ),
    ]
