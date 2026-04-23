from unittest.mock import Mock, patch

import pytest


@pytest.mark.django_db
class TestCurrencyRateService:
    def test_get_from_cache_hit(self):
        """Тест получения курса из кеша"""
        from delivery.services import CurrencyRateService

        # Создаем сервис
        service = CurrencyRateService()

        # Мокаем только метод _get_from_cache
        service._get_from_cache = Mock(return_value=92.5)
        service._fetch_from_api = Mock()

        rate = service.get_usd_rate()

        assert rate == 92.5
        service._get_from_cache.assert_called_once()
        service._fetch_from_api.assert_not_called()

    def test_get_from_cache_miss_fetch_success(self):
        """Тест получения курса из API при отсутствии в кеше"""
        from delivery.services import CurrencyRateService

        service = CurrencyRateService()
        service._get_from_cache = Mock(return_value=None)
        service._save_to_cache = Mock()
        service._fetch_from_api = Mock(return_value=91.2)

        rate = service.get_usd_rate()

        assert rate == 91.2
        service._get_from_cache.assert_called_once()
        service._fetch_from_api.assert_called_once()
        service._save_to_cache.assert_called_once_with(91.2)

    def test_get_from_cache_miss_fetch_failure(self):
        """Тест ошибки при получении курса из API"""
        from delivery.services import CurrencyRateService

        service = CurrencyRateService()
        service._get_from_cache = Mock(return_value=None)
        service._fetch_from_api = Mock(return_value=None)

        rate = service.get_usd_rate()

        assert rate is None

    def test_save_to_cache(self):
        """Тест сохранения курса в кеш"""
        from delivery.services import CurrencyRateService

        with patch('delivery.services.redis.Redis') as mock_redis:
            mock_redis_instance = Mock()
            mock_redis.return_value = mock_redis_instance

            service = CurrencyRateService()
            service._save_to_cache(93.7)

            mock_redis_instance.setex.assert_called_once()
