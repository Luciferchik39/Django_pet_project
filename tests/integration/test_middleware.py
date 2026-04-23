import pytest


@pytest.mark.django_db
class TestRequestLoggingMiddleware:
    """Интеграционные тесты для RequestLoggingMiddleware"""

    def test_middleware_does_not_break_healthcheck(self, client):
        """Тест: middleware не мешает работе healthcheck"""
        response = client.get('/api/health/')
        assert response.status_code == 200
        assert response.data.get('status') == 'healthy'

    def test_middleware_does_not_break_404(self, client):
        """Тест: middleware не мешает обработке 404"""
        response = client.get('/api/non-existent-url/')
        assert response.status_code == 404

    def test_middleware_does_not_break_parcel_creation(self, client):
        """Тест: middleware не мешает созданию посылки (даже с ошибкой)"""
        response = client.post('/api/parcels/create/', {})
        # Может быть 400 (ошибка валидации) или 415 (неверный Content-Type)
        assert response.status_code in [400, 415]

    def test_middleware_does_not_break_parcel_list(self, client):
        """Тест: middleware не мешает получению списка посылок"""
        response = client.get('/api/parcels/')
        assert response.status_code == 200

    def test_middleware_does_not_break_currency_rate(self, client):
        """Тест: middleware не мешает получению курса валют"""
        response = client.get('/api/currency-rate/')
        assert response.status_code == 200
#hi
