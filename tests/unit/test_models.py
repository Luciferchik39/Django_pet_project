from delivery.models import Parcel, ParcelType
from django.db import IntegrityError
import pytest


@pytest.mark.django_db
class TestParcelType:
    def test_parcel_type_creation(self):
        """Тест создания типа посылки"""
        parcel_type = ParcelType.objects.create(name='Бытовая техника')
        assert parcel_type.name == 'Бытовая техника'
        assert str(parcel_type) == 'Бытовая техника'

    def test_parcel_type_name_unique(self, parcel_type_electronics):
        """Тест уникальности названия типа посылки"""
        # Попытка создать дубликат должна вызвать IntegrityError
        with pytest.raises(IntegrityError):
            ParcelType.objects.create(name='Электроника')


@pytest.mark.django_db
class TestParcel:
    def test_parcel_creation(self, sample_parcel, parcel_type_electronics):
        """Тест создания посылки"""
        assert sample_parcel.name == 'Ноутбук'
        assert sample_parcel.weight == 2.5
        assert sample_parcel.parcel_type == parcel_type_electronics
        assert sample_parcel.content_value == 50000
        assert sample_parcel.delivery_cost is None
        assert str(sample_parcel) in ['Ноутбук (2.5 кг)', 'Ноутбук (2.50 кг)']

    def test_parcel_delivery_cost_calculated_property(self, sample_parcel):
        """Тест свойства is_delivery_cost_calculated"""
        assert sample_parcel.is_delivery_cost_calculated is False
        sample_parcel.delivery_cost = 350.00
        sample_parcel.save()
        assert sample_parcel.is_delivery_cost_calculated is True

    def test_parcel_ordering(self, sample_parcel, mock_session_request):
        """Тест сортировки посылок по created_at (новые сверху)"""
        # Создаем вторую посылку
        second_parcel = Parcel.objects.create(
            name='Телефон',
            weight=0.5,
            parcel_type=sample_parcel.parcel_type,
            content_value=30000,
            session_id=mock_session_request.session.session_key
        )

        # Получаем все посылки
        parcels = list(Parcel.objects.all())

        # Должно быть 2 посылки
        assert len(parcels) == 2
        assert parcels[0].id == second_parcel.id
        assert parcels[1].id == sample_parcel.id
