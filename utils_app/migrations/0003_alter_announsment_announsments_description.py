# Generated by Django 4.2.3 on 2023-11-24 06:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('utils_app', '0002_remove_announsment_announsments_title'),
    ]

    operations = [
        migrations.AlterField(
            model_name='announsment',
            name='announsments_description',
            field=models.CharField(max_length=500, null=True),
        ),
    ]
