# Generated by Django 2.1.3 on 2018-12-04 14:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hearthstone', '0004_auto_20181204_1005'),
    ]

    operations = [
        migrations.AlterField(
            model_name='card',
            name='playerClass',
            field=models.TextField(default='NaN', max_length=50),
        ),
    ]