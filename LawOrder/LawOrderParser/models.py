from django.db import models
from django.urls import reverse
from django.utils import timezone

class Documents(models.Model):
    document_id = models.CharField(max_length=155, verbose_name='Номер документа')
    document_date = models.DateField(verbose_name='Дата документа')
    document_title = models.CharField(max_length=255, verbose_name='Заголовок')
    slug = models.SlugField(max_length=455, unique=True, db_index=True, verbose_name="URL")
    document_city = models.CharField(max_length=155, verbose_name='Город')
    document_tribunal = models.CharField(max_length=155, verbose_name='Суд')
    document_judge = models.CharField(max_length=155, verbose_name='Судья')
    document_content = models.TextField(blank=True, verbose_name='Текст документа')
    # document_instance = models.CharField(default=None, max_length=100, verbose_name="Инстанция длкумента")
    time_create = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    time_update = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    is_published = models.BooleanField(default=True, verbose_name='Публикация документа')
    cat = models.ForeignKey('Category', on_delete=models.PROTECT, verbose_name='Категория документа')
    inst = models.ForeignKey('Instance', blank=True, null=True, on_delete=models.PROTECT, verbose_name='Инстанция документа')

    def __str__(self):
        return self.document_title
    def get_absolute_url(self):
        return reverse('document', kwargs={'document_slug': self.slug})
    class Meta:
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'
        #сортировка по времени создания и заголовку, она применится и на основной части сайта
        ordering = ['-document_date', 'document_id', 'time_create', 'document_title']

class Category(models.Model):
    name = models.CharField(max_length=100, db_index=True, verbose_name='Категория')
    category_tag = models.CharField(default=None, max_length=100, db_index=True, verbose_name='Тег категории')
    slug = models.SlugField(max_length=255, unique=True, db_index=True, verbose_name="URL")
    def __str__(self):
        return self.name
    def get_absolute_url(self):
        return reverse('category', kwargs={'cat_slug': self.slug})
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категория'
        ordering = ['id']

class Instance(models.Model):
    name = models.CharField(max_length=100, db_index=True, verbose_name='Инстанция')
    instance_tag = models.CharField(default=None, max_length=100, db_index=True, verbose_name='Тег инстанции')
    slug = models.SlugField(max_length=255, unique=True, db_index=True, verbose_name="URL")
    def __str__(self):
        return self.name
    def get_absolute_url(self):
        return reverse('instance', kwargs={'inst_slug': self.slug})
    class Meta:
        verbose_name = 'Инстанция'
        verbose_name_plural = 'Инстанции'
        ordering = ['id']

class Region(models.Model):
    region_name = models.CharField(max_length=100, verbose_name="Название региона")
    arbitral_region = models.DecimalField(max_digits=9, decimal_places=0, blank=True, null=True, verbose_name="Код региона для арбитражных судов")
    regular_region = models.DecimalField(max_digits=9, decimal_places=0, blank=True, null=True, verbose_name="Код региона для судов общей юрисдикции")
    magistrate_region = models.DecimalField(max_digits=9, decimal_places=0, blank=True, null=True, verbose_name="Код региона для мировых судов")
    city_created_at = models.DateTimeField(auto_now_add=True)
    city_updated_at = models.DateTimeField(auto_now=True)


#пользователи телеграм
class TelegramSubscriber(models.Model):
    #данные пользователя
    chat_id = models.CharField(max_length=255, unique=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    subscribed_to_categories = models.ManyToManyField('Category', blank=True, verbose_name='Доступ к категориии документов')
    def __str__(self):
        return f'{self.username} ({self.chat_id})'
    class Meta:
        verbose_name = 'Подписчик Telegram'
        verbose_name_plural = 'Подписчики Telegram'
        ordering = ['subscribed_at']
