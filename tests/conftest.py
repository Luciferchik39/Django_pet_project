from decimal import Decimal

from delivery.models import Parcel, ParcelType
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import Client, RequestFactory
import pytest


@pytest.fixture
def api_client():
    """API клиент для тестов"""
    return Client()


@pytest.fixture
def request_factory():
    """RequestFactory для тестирования middleware"""
    return RequestFactory()


@pytest.fixture
def mock_session_request(request_factory):
    """Request с созданной сессией"""
    request = request_factory.get('/')
    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()
    return request


@pytest.fixture
def parcel_type_electronics(db):
    """Фикстура типа посылки 'Электроника'"""
    return ParcelType.objects.get_or_create(name='Электроника')[0]


@pytest.fixture
def parcel_type_clothes(db):
    """Фикстура типа посылки 'Одежда'"""
    return ParcelType.objects.get_or_create(name='Одежда')[0]


@pytest.fixture
def parcel_type_other(db):
    """Фикстура типа посылки 'Разное'"""
    return ParcelType.objects.get_or_create(name='Разное')[0]


@pytest.fixture
def sample_parcel(db, parcel_type_electronics, mock_session_request):
    """Фикстура созданной посылки"""
    return Parcel.objects.create(
        name='Ноутбук',
        weight=Decimal('2.5'),
        parcel_type=parcel_type_electronics,
        content_value=Decimal('50000'),
        session_id=mock_session_request.session.session_key
    )


@pytest.fixture
def sample_parcels_list(db, parcel_type_electronics, parcel_type_clothes, mock_session_request):
    """Список посылок для тестирования пагинации и фильтров"""
    session_id = mock_session_request.session.session_key
    parcels = []
    for i in range(5):
        delivery_cost = None if i < 3 else Decimal('500')
        parcels.append(Parcel.objects.create(
            name=f'Посылка {i}',
            weight=Decimal('1.0'),
            parcel_type=parcel_type_electronics if i % 2 == 0 else parcel_type_clothes,
            content_value=Decimal('1000'),
            session_id=session_id,
            delivery_cost=delivery_cost
        ))
    return parcels
#hi
