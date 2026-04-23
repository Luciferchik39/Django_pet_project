# apps/delivery/services.py
"""
Сервисы для работы с внешними API и кешированием
"""

from datetime import datetime
import json

from django.conf import settings
from loguru import logger
import redis
import requests


class CurrencyRateService:
    """Сервис для получения курса валют с кешированием в Redis"""

    def __init__(self):
        """Инициализация подключения к Redis"""
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        self.cache_key = "usd_rub_rate"
        self.cache_ttl = settings.CACHE_TTL

        logger.info(f"CurrencyRateService инициализирован с Redis на {settings.REDIS_HOST}:{settings.REDIS_PORT}")

    def get_usd_rate(self) -> float | None:
        """Получить курс USD/RUB."""
        cached_rate = self._get_from_cache()
        if cached_rate is not None:
            logger.info(f"Курс USD/RUB получен из кеша: {cached_rate}")
            return cached_rate

        logger.debug("Курс не найден в кеше, запрашиваем из API")
        rate = self._fetch_from_api()
        if rate is not None:
            self._save_to_cache(rate)
            logger.success(f"Курс USD/RUB получен из API и сохранен в кеш: {rate}")
        else:
            logger.error("Не удалось получить курс USD/RUB из API")

        return rate

    def _get_from_cache(self) -> float | None:
        """Получить курс из Redis кеша"""
        try:
            cached_data = self.redis_client.get(self.cache_key)
            if cached_data:
                data = json.loads(cached_data)  # type: ignore
                cached_time = datetime.fromisoformat(data['timestamp'])
                age = (datetime.now() - cached_time).seconds
                if age < self.cache_ttl:
                    logger.debug(f"Кеш актуален (возраст: {age} сек)")
                    return float(data['rate'])
                else:
                    logger.debug(f"Кеш устарел (возраст: {age} сек)")
        except Exception as e:
            logger.warning(f"Ошибка при чтении из Redis: {e}")
        return None

    def _save_to_cache(self, rate: float) -> None:
        """Сохранить курс в Redis кеш"""
        try:
            cache_data = {
                'rate': str(rate),
                'timestamp': datetime.now().isoformat()
            }
            self.redis_client.setex(
                self.cache_key,
                self.cache_ttl,
                json.dumps(cache_data)
            )
            logger.debug(f"Курс сохранен в кеш на {self.cache_ttl} сек")
        except Exception as e:
            logger.warning(f"Ошибка при сохранении в Redis: {e}")

    def _fetch_from_api(self) -> float | None:
        """Запросить курс USD/RUB из внешнего API."""
        url = "https://cbr-xml-daily.ru/daily_json.js"

        try:
            logger.debug(f"Запрос к API: {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            usd_rate = data['Valute']['USD']['Value']

            logger.info(f"Успешный ответ от API: USD/RUB = {usd_rate}")
            return float(usd_rate)

        except requests.exceptions.Timeout:
            logger.error("Таймаут при запросе к API курсов (10 сек)")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("Ошибка подключения к API курсов")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка HTTP запроса: {e}")
            return None
        except KeyError as e:
            logger.error(f"Неожиданный формат ответа от API: {e}")
            return None
        except Exception as e:
            logger.error(f"Неизвестная ошибка при получении курса: {e}")
            return None

    def clear_cache(self) -> bool:
        """Очистить кеш курса валют"""
        try:
            self.redis_client.delete(self.cache_key)
            logger.info("Кеш курса валют очищен")
            return True
        except Exception as e:
            logger.error(f"Ошибка при очистке кеша: {e}")
            return False

    def get_cache_info(self) -> dict:
        """Получить информацию о кеше (для отладки)"""
        try:
            cached_data = self.redis_client.get(self.cache_key)
            if cached_data:
                data = json.loads(cached_data)  # type: ignore
                return {
                    'cached': True,
                    'rate': float(data['rate']),
                    'timestamp': data['timestamp'],
                    'ttl': self.redis_client.ttl(self.cache_key)
                }
            return {'cached': False}
        except Exception as e:
            logger.error(f"Ошибка получения информации о кеше: {e}")
            return {'cached': False, 'error': str(e)}


# Создаем глобальный экземпляр сервиса
currency_service = CurrencyRateService()
