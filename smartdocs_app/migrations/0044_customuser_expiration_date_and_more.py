# Generated by Django 5.0.1 on 2024-08-22 19:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("smartdocs_app", "0043_customuser_role_alter_customuser_first_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="expiration_date",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="customuser",
            name="last_name",
            field=models.CharField(max_length=30),
        ),
    ]
