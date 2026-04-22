# apps/delivery/tasks.py
"""
Celery задачи для расчета стоимости доставки
"""
from decimal import Decimal
from typing import Any

from celery import shared_task  # type: ignore
from django.db import transaction
from loguru import logger

from .models import Parcel
from .services import currency_service


def calculate_delivery_cost(parcel: Parcel) -> Decimal:
    """
    Рассчитать стоимость доставки для одной посылки.

    Формула расчета:
    - Базовая стоимость: 100 руб
    - За вес: 50 руб/кг
    - Коэффициенты типа: Электроника x1.3, Одежда x1.1, Разное x1.0
    - Страховка: 5% от стоимости содержимого
    """
    # Базовая стоимость
    base_cost = Decimal('100')

    # Стоимость за вес (50 руб/кг)
    weight_cost = parcel.weight * Decimal('50')

    # Коэффициент типа посылки
    type_coefficient = Decimal('1.0')
    if parcel.parcel_type.name == 'Электроника':
        type_coefficient = Decimal('1.3')
    elif parcel.parcel_type.name == 'Одежда':
        type_coefficient = Decimal('1.1')

    # Страховка (5% от стоимости содержимого)
    insurance = parcel.content_value * Decimal('0.05')

    # Полная стоимость
    total: Decimal = (base_cost + weight_cost) * type_coefficient + insurance

    return total.quantize(Decimal('0.01'))


@shared_task
def calculate_parcel_delivery_cost(parcel_id: int) -> dict[str, Any]:
    """
    Рассчитать стоимость доставки для конкретной посылки.

    Args:
        parcel_id: ID посылки

    Returns:
        dict: Результат расчета
    """
    logger.info(f"Начинаем расчет стоимости для посылки ID={parcel_id}")

    try:
        parcel = Parcel.objects.get(id=parcel_id)

        # Получаем курс валют (опционально, для будущего использования)
        usd_rate = currency_service.get_usd_rate()

        # Рассчитываем стоимость
        delivery_cost = calculate_delivery_cost(parcel)

        # Сохраняем результат
        with transaction.atomic():
            parcel.delivery_cost = delivery_cost
            parcel.save(update_fields=['delivery_cost'])

        logger.success(
            f"Стоимость доставки для посылки '{parcel.name}' (ID={parcel_id}) "
            f"рассчитана: {delivery_cost} руб. Курс USD: {usd_rate}"
        )

        return {
            'parcel_id': parcel_id,
            'name': parcel.name,
            'delivery_cost': str(delivery_cost),
            'usd_rate': usd_rate,
            'status': 'success'
        }

    except Parcel.DoesNotExist:
        logger.error(f"Посылка с ID={parcel_id} не найдена")
        return {
            'parcel_id': parcel_id,
            'status': 'error',
            'error': 'Parcel not found'
        }
    except Exception as e:
        logger.error(f"Ошибка при расчете стоимости для посылки {parcel_id}: {e}")
        return {
            'parcel_id': parcel_id,
            'status': 'error',
            'error': str(e)
        }


@shared_task
def calculate_all_parcels_delivery_cost() -> dict[str, Any]:
    """
    Рассчитать стоимость доставки для всех посылок с null стоимостью.
    Запускается периодически каждые 5 минут.

    Returns:
        dict: Статистика выполнения
    """
    logger.info("Запуск периодической задачи расчета стоимости для всех посылок")

    # Находим все посылки, у которых стоимость доставки не рассчитана
    parcels = Parcel.objects.filter(delivery_cost__isnull=True)
    total_count = parcels.count()

    if total_count == 0:
        logger.info("Нет посылок для расчета стоимости")
        return {
            'total': 0,
            'success': 0,
            'failed': 0,
            'message': 'No parcels to calculate'
        }

    logger.info(f"Найдено {total_count} посылок для расчета")

    success_count = 0
    failed_count = 0
    errors: list = []

    for parcel in parcels:
        try:
            # Вызываем задачу синхронно для каждой посылки
            parcel_id = parcel.id
            result = calculate_parcel_delivery_cost(parcel_id)
            if result.get('status') == 'success':
                success_count += 1
            else:
                failed_count += 1
                errors.append(result)
        except Exception as e:
            failed_count += 1
            errors.append({'parcel_id': parcel.id, 'error': str(e)})
            logger.error(f"Ошибка при обработке посылки {parcel.id}: {e}")

    logger.success(
        f"Периодическая задача завершена. "
        f"Успешно: {success_count}, Ошибок: {failed_count}, Всего: {total_count}"
    )

    return {
        'total': total_count,
        'success': success_count,
        'failed': failed_count,
        'errors': errors[:10]  # Возвращаем только первые 10 ошибок
    }


@shared_task
def calculate_parcels_for_session(session_id: str) -> dict[str, Any]:
    """
    Рассчитать стоимость для всех посылок конкретной сессии.

    Args:
        session_id: ID сессии пользователя

    Returns:
        dict: Статистика выполнения
    """
    logger.info(f"Запуск расчета стоимости для сессии {session_id}")

    parcels = Parcel.objects.filter(session_id=session_id, delivery_cost__isnull=True)
    total_count = parcels.count()

    if total_count == 0:
        logger.info(f"Нет посылок для расчета в сессии {session_id}")
        return {
            'session_id': session_id,
            'total': 0,
            'success': 0,
            'failed': 0
        }

    success_count = 0
    failed_count = 0

    for parcel in parcels:
        try:
            result = calculate_parcel_delivery_cost(parcel.id)
            if result.get('status') == 'success':
                success_count += 1
            else:
                failed_count += 1
        except Exception as e:
            failed_count += 1
            logger.error(f"Ошибка: {e}")

    logger.success(
        f"Расчет для сессии {session_id} завершен. "
        f"Успешно: {success_count}, Ошибок: {failed_count}"
    )

    return {
        'session_id': session_id,
        'total': total_count,
        'success': success_count,
        'failed': failed_count
    }
