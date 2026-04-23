from unittest.mock import patch

import pytest


@pytest.mark.django_db
class TestHealthCheck:
    """Интеграционные тесты healthcheck"""

    def test_healthcheck_ok(self, client):
        """Тест успешного healthcheck когда все сервисы работают"""
        with patch('django.db.backends.base.base.BaseDatabaseWrapper.ensure_connection') as mock_db, \
                patch('delivery.services.redis.Redis.ping') as mock_redis, \
                patch('config.celery.app.control.ping') as mock_celery:
            mock_db.return_value = None
            mock_redis.return_value = True
            mock_celery.return_value = [{'ok': 'pong'}]

            response = client.get('/api/health/')

            assert response.status_code == 200
            assert response.data.get('status') == 'healthy'

            checks = response.data.get('checks', {})
            assert checks.get('postgresql') == 'ok'
            assert checks.get('redis') == 'ok'
            assert checks.get('celery') == 'ok'
            assert checks.get('django') == 'ok'

    def test_healthcheck_db_failure(self, client):
        """Тест healthcheck когда БД недоступна"""
        with patch('django.db.backends.base.base.BaseDatabaseWrapper.ensure_connection',
                   side_effect=Exception('DB Error')):
            response = client.get('/api/health/')

            assert response.status_code == 500
            assert 'error' in response.data

    def test_healthcheck_redis_failure(self, client):
        """Тест healthcheck когда Redis недоступен"""
        with patch('django.db.backends.base.base.BaseDatabaseWrapper.ensure_connection') as mock_db, \
                patch('delivery.services.redis.Redis.ping', side_effect=Exception('Redis Error')):
            mock_db.return_value = None

            response = client.get('/api/health/')
            assert response.status_code == 200
            assert response.data.get('status') == 'healthy'

            checks = response.data.get('checks', {})
            assert checks.get('postgresql') == 'ok'
            assert checks.get('redis') == 'error'
            assert checks.get('django') == 'ok'

    def test_healthcheck_celery_failure(self, client):
        """Тест healthcheck когда Celery недоступен"""
        with patch('django.db.backends.base.base.BaseDatabaseWrapper.ensure_connection') as mock_db, \
                patch('delivery.services.redis.Redis.ping') as mock_redis, \
                patch('config.celery.app.control.ping', side_effect=Exception('Celery Error')):
            mock_db.return_value = None
            mock_redis.return_value = True

            response = client.get('/api/health/')

            assert response.status_code == 200
            assert response.data.get('status') == 'healthy'

            checks = response.data.get('checks', {})
            assert checks.get('postgresql') == 'ok'
            assert checks.get('redis') == 'ok'
            assert checks.get('celery') == 'error'
            assert checks.get('django') == 'ok'
#hi
