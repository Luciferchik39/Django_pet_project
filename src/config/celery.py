# src/config/celery.py
"""
Celery конфигурация для Django проекта
"""
import os

from celery import Celery
from loguru import logger

# Устанавливаем модуль настроек Django по умолчанию
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Создаем экземпляр Celery
app = Celery('delivery_service')

# Загружаем настройки из Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически находим задачи в приложениях
app.autodiscover_tasks()

# Настройка логирования Celery
logger.info("Celery приложение инициализировано")


@app.task(bind=True)
def debug_task(self):
    """Отладочная задача для проверки работы Celery"""
    logger.info(f'Request: {self.request!r}')
    return 'Celery работает!'
