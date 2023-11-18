# Generated by Django 4.2.3 on 2023-11-16 11:28

from django.db import migrations, models
import uuid
import visitors_app.models


class Migration(migrations.Migration):

    dependencies = [
        ('visitors_app', '0009_alter_visitorsmanagement_delete_flag'),
    ]

    operations = [
        migrations.CreateModel(
            name='VisitorPhoto',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('visitor_pass_id', models.UUIDField()),
                ('image', models.ImageField(upload_to=visitors_app.models.upload_path)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('delete_flag', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'visitors_photo_master',
            },
        ),
    ]
