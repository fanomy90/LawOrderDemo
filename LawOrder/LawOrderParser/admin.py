from django.contrib import admin
from django import forms
from .models import *
# Register your models here.
class TelegramSubscriberForm(forms.ModelForm):
    class Meta:
        model = TelegramSubscriber
        fields = '__all__'

class DocumentsAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'document_id', 
        'slug', 
        'document_title', 
        'document_date',
        'get_category_name', 
        'time_create', 
        'document_date',
        'document_city', 
        'document_tribunal',
        'document_judge',
        'document_instance',
        'is_published'
        )
    list_display_links = ('id', 'document_title')
    #Доп поля по которым можно произвести поиск
    search_fields = (
        'document_title', 
        'cat__name', 
        'document_date', 
        'document_city', 
        'document_tribunal',
        'document_judge',
        'document_instance'
        )
    #Разрешение редактирования параметра публикации в админке
    list_editable = ('is_published', )
    #Возможность фильтрации записей в админке по публикации и дате создания
    list_filter = (
        'cat', 
        'is_published', 
        'document_date', 
        'document_city', 
        'document_tribunal',
        'document_judge',
        'document_instance'
        )
    #Автоматическое создание слага по введенному полю в админке
    prepopulated_fields = {"slug": ("document_title",)}

    def get_category_name(self, obj):
        return obj.cat.name  # Возвращаем имя категории
    get_category_name.short_description = 'Категория'  # Задаем название столбца в админке

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'slug', 'name')
    list_display_links = ('id', 'name')
    #так как передаем кортеж то для одного элемента надо поставить запятую
    search_fields = ('name',)
    prepopulated_fields = {"slug": ("name",)}

class RegionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'region_name', 
        'arbitral_region', 
        'regular_region',
        'magistrate_region'
        )
    search_fields = ('region_name',)
    list_editable = (
        'region_name', 
        'arbitral_region', 
        'regular_region',
        'magistrate_region'
        )
    
class TelegramSubscriberAdmin(admin.ModelAdmin):
    #вызов кастомной форме для админки для динамической загрузки внещних файловы
    form = TelegramSubscriberForm
    list_display = ('chat_id', 'username', 'get_subscribed_categories', 'subscribed_at')
    list_display_links = ('chat_id', 'username')
    #так как передаем кортеж то для одного элемента надо поставить запятую
    search_fields = ('username',)
    # list_editable = ('subscribed_to_categories',)
    # Метод для отображения категорий в списке
    def get_subscribed_categories(self, obj):
        return ", ".join([cat.name for cat in obj.subscribed_to_categories.all()])
    get_subscribed_categories.short_description = 'Категории новостей'
    
admin.site.register(Documents, DocumentsAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(TelegramSubscriber, TelegramSubscriberAdmin)
admin.site.register(Region, RegionAdmin)

admin.site.site_header = "Панель управления документами Law&Order"
admin.site.site_title = "Админка Law&Order"
admin.site.index_title = "Добро пожаловать в админку Law&Order"