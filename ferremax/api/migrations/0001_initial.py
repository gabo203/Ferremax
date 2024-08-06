# Generated by Django 5.0.6 on 2024-08-02 03:53

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Producto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo_producto', models.CharField(max_length=255)),
                ('marca', models.CharField(max_length=255)),
                ('codigo', models.CharField(max_length=255)),
                ('nombre', models.CharField(max_length=255)),
                ('precio', models.PositiveIntegerField()),
            ],
        ),
    ]
