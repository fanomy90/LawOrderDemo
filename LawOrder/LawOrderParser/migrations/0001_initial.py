# Generated by Django 5.1.4 on 2025-01-08 15:38

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=100, verbose_name='Категория')),
                ('slug', models.SlugField(max_length=255, unique=True, verbose_name='URL')),
            ],
            options={
                'verbose_name': 'Категория',
                'verbose_name_plural': 'Категория',
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('region_name', models.CharField(max_length=100, verbose_name='Название региона')),
                ('arbitral_region', models.DecimalField(blank=True, decimal_places=0, max_digits=9, null=True, verbose_name='Код региона для арбитражных судов')),
                ('regular_region', models.DecimalField(blank=True, decimal_places=0, max_digits=9, null=True, verbose_name='Код региона для судов общей юрисдикции')),
                ('magistrate_region', models.DecimalField(blank=True, decimal_places=0, max_digits=9, null=True, verbose_name='Код региона для мировых судов')),
                ('city_created_at', models.DateTimeField(auto_now_add=True)),
                ('city_updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Documents',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('document_id', models.CharField(max_length=155, verbose_name='Номер документа')),
                ('document_date', models.DateField(verbose_name='Дата документа')),
                ('document_title', models.CharField(max_length=255, verbose_name='Заголовок')),
                ('slug', models.SlugField(max_length=455, unique=True, verbose_name='URL')),
                ('document_city', models.CharField(max_length=155, verbose_name='Город')),
                ('document_tribunal', models.CharField(max_length=155, verbose_name='Суд')),
                ('document_judge', models.CharField(max_length=155, verbose_name='Судья')),
                ('document_content', models.TextField(blank=True, verbose_name='Текст документа')),
                ('document_instance', models.CharField(default=None, max_length=100, verbose_name='Инстанция длкумента')),
                ('time_create', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('time_update', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
                ('is_published', models.BooleanField(default=True, verbose_name='Публикация документа')),
                ('cat', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='LawOrderParser.category', verbose_name='Категория документа')),
            ],
            options={
                'verbose_name': 'Документ',
                'verbose_name_plural': 'Документы',
                'ordering': ['-document_date', 'document_id', 'time_create', 'document_title'],
            },
        ),
        migrations.CreateModel(
            name='TelegramSubscriber',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chat_id', models.CharField(max_length=255, unique=True)),
                ('username', models.CharField(blank=True, max_length=255, null=True)),
                ('subscribed_at', models.DateTimeField(auto_now_add=True)),
                ('subscribed_to_categories', models.ManyToManyField(blank=True, to='LawOrderParser.category', verbose_name='Доступ к категориии документов')),
            ],
            options={
                'verbose_name': 'Подписчик Telegram',
                'verbose_name_plural': 'Подписчики Telegram',
                'ordering': ['subscribed_at'],
            },
        ),
    ]
