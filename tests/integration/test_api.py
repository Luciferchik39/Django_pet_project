from decimal import Decimal

from delivery.models import Parcel, ParcelType
import pytest


@pytest.mark.django_db
class TestParcelAPI:
    """Интеграционные тесты API посылок"""

    def test_create_parcel_success(self, client, db):
        """Тест успешного создания посылки"""
        # Создаем тип посылки
        ParcelType.objects.create(name='Электроника')

        response = client.post(
            '/api/parcels/create/',
            {
                'name': 'Телефон',
                'weight': 0.5,
                'parcel_type_name': 'Электроника',
                'content_value': 30000
            },
            content_type='application/json'  # Добавляем content_type
        )
        assert response.status_code == 201
        assert 'id' in response.data
        assert response.data['message'] == 'Посылка успешно создана'

    def test_create_parcel_invalid_data(self, client):
        """Тест создания посылки с невалидными данными"""
        response = client.post(
            '/api/parcels/create/',
            {
                'name': '',
                'weight': -5,
                'parcel_type_name': 'Электроника',
                'content_value': 30000
            },
            content_type='application/json'  # Добавляем content_type
        )
        assert response.status_code == 400
        assert 'errors' in response.data

    def test_parcels_list_pagination(self, client, db):
        """Тест пагинации списка посылок"""
        # Создаем тип посылки
        parcel_type = ParcelType.objects.create(name='Электроника')

        # Создаем сессию и получаем ее ключ
        session = client.session
        session.save()
        session_key = session.session_key

        # Создаем тестовые посылки с ключом сессии
        for i in range(5):
            Parcel.objects.create(
                name=f'Посылка {i}',
                weight=Decimal('1.0'),
                parcel_type=parcel_type,
                content_value=Decimal('1000'),
                session_id=session_key  # Используем реальный ключ сессии
            )

        response = client.get('/api/parcels/?page=1&page_size=2')
        assert response.status_code == 200
        assert len(response.data['results']) == 2
        assert response.data['count'] == 5

    def test_parcels_list_filter_by_type(self, client, db):
        """Тест фильтрации по типу посылки"""
        # Создаем типы посылок
        electronics = ParcelType.objects.create(name='Электроника')
        clothes = ParcelType.objects.create(name='Одежда')

        session_id = 'test_session_123'

        # Создаем посылки разных типов
        Parcel.objects.create(
            name='Ноутбук',
            weight=Decimal('2.0'),
            parcel_type=electronics,
            content_value=Decimal('50000'),
            session_id=session_id
        )
        Parcel.objects.create(
            name='Футболка',
            weight=Decimal('0.5'),
            parcel_type=clothes,
            content_value=Decimal('2000'),
            session_id=session_id
        )

        response = client.get(f'/api/parcels/?parcel_type={electronics.id}')
        assert response.status_code == 200
        for parcel in response.data['results']:
            assert parcel['parcel_type']['id'] == electronics.id

    def test_parcel_detail_success(self, client, db):
        """Тест получения деталей посылки"""
        parcel_type = ParcelType.objects.create(name='Электроника')

        # Создаем сессию и получаем ее ключ
        session = client.session
        session.save()
        session_key = session.session_key

        # Создаем посылку с ключом сессии
        parcel = Parcel.objects.create(
            name='Ноутбук',
            weight=Decimal('2.5'),
            parcel_type=parcel_type,
            content_value=Decimal('50000'),
            session_id=session_key  # Используем реальный ключ сессии
        )

        response = client.get(f'/api/parcels/{parcel.id}/')
        assert response.status_code == 200
        assert response.data['id'] == parcel.id
        assert response.data['name'] == parcel.name

    def test_parcel_detail_not_found(self, client):
        """Тест получения несуществующей посылки"""
        response = client.get('/api/parcels/99999/')
        assert response.status_code == 404
        assert 'error' in response.data

    def test_calculate_single_parcel_manual(self, client, db):
        """Тест ручного запуска расчета для одной посылки"""
        parcel_type = ParcelType.objects.create(name='Электроника')

        # Создаем сессию и получаем ее ключ
        session = client.session
        session.save()
        session_key = session.session_key

        # Создаем посылку с ключом сессии
        parcel = Parcel.objects.create(
            name='Ноутбук',
            weight=Decimal('2.5'),
            parcel_type=parcel_type,
            content_value=Decimal('50000'),
            session_id=session_key,
            delivery_cost=None
        )

        response = client.post(f'/api/parcels/{parcel.id}/calculate/')
        # API возвращает 202 Accepted для асинхронных задач
        assert response.status_code == 202
        # Проверяем, что задача принята
        assert 'task_id' in response.data or 'message' in response.data

@pytest.mark.django_db
class TestCurrencyRateAPI:
    """Интеграционные тесты API курса валют"""

    def test_get_currency_rate(self, client):
        """Тест получения курса валют"""
        response = client.get('/api/currency-rate/')
        assert response.status_code == 200
        assert 'rate' in response.data
        # Курс должен быть положительным числом
        assert response.data['rate'] > 0

    def test_clear_currency_cache(self, client):
        """Тест очистки кеша курса валют"""
        # Сначала получаем курс (кешируется)
        response1 = client.get('/api/currency-rate/')
        assert response1.status_code == 200

        # Очищаем кеш
        response2 = client.delete('/api/currency-rate/cache/')
        assert response2.status_code == 200
#hi
