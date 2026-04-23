# apps/delivery/models.py
from django.db import models
from django.db.models import CharField, DateTimeField, DecimalField, ForeignKey


class ParcelType(models.Model):
    """Типы посылок"""

    name: CharField = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Название типа"
    )

    class Meta:
        verbose_name = "Тип посылки"
        verbose_name_plural = "Типы посылок"
        ordering = ['name']

    def __str__(self) -> str:
        return str(self.name)


class Parcel(models.Model):
    """Посылка"""

    # Основные поля
    name: CharField = models.CharField(
        max_length=200,
        verbose_name="Название посылки"
    )

    weight: DecimalField = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Вес (кг)"
    )

    parcel_type: ForeignKey = models.ForeignKey(
        ParcelType,
        on_delete=models.PROTECT,
        related_name='parcels',
        verbose_name="Тип посылки"
    )

    content_value: DecimalField = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Стоимость содержимого (руб)"
    )

    session_id: CharField = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name="ID сессии пользователя"
    )

    delivery_cost: DecimalField = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Стоимость доставки (руб)"
    )

    created_at: DateTimeField = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )

    updated_at: DateTimeField = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )

    class Meta:
        verbose_name = "Посылка"
        verbose_name_plural = "Посылки"
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.name} ({self.weight} кг)"

    @property
    def is_delivery_cost_calculated(self) -> bool:
        """Проверяет, рассчитана ли стоимость доставки"""
        return self.delivery_cost is not None
