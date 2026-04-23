from delivery.serializers import ParcelCreateSerializer, ParcelResponseSerializer
import pytest


@pytest.mark.django_db
class TestParcelCreateSerializer:
    def test_valid_serializer(self, parcel_type_electronics, mock_session_request):
        data = {
            'name': 'Телефон',
            'weight': 0.5,
            'parcel_type_name': 'Электроника',
            'content_value': 30000
        }
        serializer = ParcelCreateSerializer(data=data, context={'session_id': mock_session_request.session.session_key})
        assert serializer.is_valid()
        parcel = serializer.save()
        assert parcel.name == 'Телефон'
        assert parcel.weight == 0.5

    def test_invalid_name_empty(self, parcel_type_electronics, mock_session_request):
        data = {
            'name': '   ',
            'weight': 0.5,
            'parcel_type_name': 'Электроника',
            'content_value': 30000
        }
        serializer = ParcelCreateSerializer(data=data, context={'session_id': mock_session_request.session.session_key})
        assert not serializer.is_valid()
        assert 'name' in serializer.errors

    def test_invalid_weight_zero(self, parcel_type_electronics, mock_session_request):
        data = {
            'name': 'Телефон',
            'weight': 0,
            'parcel_type_name': 'Электроника',
            'content_value': 30000
        }
        serializer = ParcelCreateSerializer(data=data, context={'session_id': mock_session_request.session.session_key})
        assert not serializer.is_valid()
        assert 'weight' in serializer.errors

    def test_invalid_weight_negative(self, parcel_type_electronics, mock_session_request):
        data = {
            'name': 'Телефон',
            'weight': -5,
            'parcel_type_name': 'Электроника',
            'content_value': 30000
        }
        serializer = ParcelCreateSerializer(data=data, context={'session_id': mock_session_request.session.session_key})
        assert not serializer.is_valid()
        assert 'weight' in serializer.errors

    def test_invalid_content_value_negative(self, parcel_type_electronics, mock_session_request):
        data = {
            'name': 'Телефон',
            'weight': 0.5,
            'parcel_type_name': 'Электроника',
            'content_value': -100
        }
        serializer = ParcelCreateSerializer(data=data, context={'session_id': mock_session_request.session.session_key})
        assert not serializer.is_valid()
        assert 'content_value' in serializer.errors

    def test_parcel_type_not_found(self, mock_session_request):
        data = {
            'name': 'Телефон',
            'weight': 0.5,
            'parcel_type_name': 'Несуществующий тип',
            'content_value': 30000
        }
        serializer = ParcelCreateSerializer(data=data, context={'session_id': mock_session_request.session.session_key})
        assert not serializer.is_valid()
        assert 'parcel_type_name' in serializer.errors


@pytest.mark.django_db
class TestParcelResponseSerializer:
    def test_serializer_without_delivery_cost(self, sample_parcel):
        serializer = ParcelResponseSerializer(sample_parcel)
        assert serializer.data['delivery_status'] == 'Не рассчитано'
        assert serializer.data['delivery_cost'] is None

    def test_serializer_with_delivery_cost(self, sample_parcel):
        sample_parcel.delivery_cost = 350
        sample_parcel.save()
        serializer = ParcelResponseSerializer(sample_parcel)
        assert serializer.data['delivery_status'] == 'Рассчитано: 350 руб'
        assert serializer.data['delivery_cost'] == '350.00'
