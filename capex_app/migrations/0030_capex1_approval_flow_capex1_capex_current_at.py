# Generated by Django 4.2.3 on 2023-10-31 09:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('capex_app', '0029_alter_capex1_budget_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='capex1',
            name='approval_flow',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='capex1',
            name='capex_current_at',
            field=models.CharField(max_length=50, null=True),
        ),
    ]
