# Generated by Django 4.2.3 on 2023-10-10 17:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('capex_app', '0012_alter_capex1_asset_list'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='capex1',
            name='asset_list',
        ),
    ]
