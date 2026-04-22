from delivery.models import Parcel, ParcelType
import pytest


@pytest.mark.django_db
class TestParcelType:
    def test_parcel_type_creation(self):
        parcel_type = ParcelType.objects.create(name='Электроника')
        assert parcel_type.name == 'Электроника'
        assert str(parcel_type) == 'Электроника'

    def test_parcel_type_name_unique(self, parcel_type_electronics):
        with pytest.raises(Exception):
            ParcelType.objects.create(name='Электроника')


@pytest.mark.django_db
class TestParcel:
    def test_parcel_creation(self, sample_parcel, parcel_type_electronics):
        assert sample_parcel.name == 'Ноутбук'
        assert sample_parcel.weight == 2.5
        assert sample_parcel.parcel_type == parcel_type_electronics
        assert sample_parcel.content_value == 50000
        assert sample_parcel.delivery_cost is None
        assert str(sample_parcel) == 'Ноутбук (2.50 кг)'

    def test_parcel_delivery_cost_calculated_property(self, sample_parcel):
        assert sample_parcel.is_delivery_cost_calculated is False
        sample_parcel.delivery_cost = 350.00
        sample_parcel.save()
        assert sample_parcel.is_delivery_cost_calculated is True

    def test_parcel_ordering(self, sample_parcel, mock_session_request):
        parcel2 = Parcel.objects.create(
            name='Телефон',
            weight=0.5,
            parcel_type=sample_parcel.parcel_type,
            content_value=30000,
            session_id=mock_session_request.session.session_key
        )
        parcels = list(Parcel.objects.all())
        assert parcels[0].created_at >= parcels[1].created_at
