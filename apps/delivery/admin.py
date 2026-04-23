from django.contrib import admin

# Register your models here.
# apps/delivery/admin.py
from .models import Parcel, ParcelType

#hi

@admin.register(ParcelType)
class ParcelTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Parcel)
class ParcelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'weight', 'parcel_type', 'content_value',
                    'delivery_cost', 'session_id', 'created_at')
    list_filter = ('parcel_type', 'created_at')
    search_fields = ('name', 'session_id')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'weight', 'parcel_type', 'content_value')
        }),
        ('Доставка', {
            'fields': ('delivery_cost',)
        }),
        ('Пользователь', {
            'fields': ('session_id',)
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
