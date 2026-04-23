from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

from delivery.tasks import calculate_delivery_cost
import pytest


class TestDeliveryCostCalculation:
    """Тесты формулы расчета стоимости доставки"""

    def test_calculate_cost_electronics(self):
        mock_parcel = MagicMock()
        mock_parcel.weight = Decimal('2.0')
        mock_parcel.content_value = Decimal('10000')
        mock_parcel.parcel_type.name = 'Электроника'

        cost = calculate_delivery_cost(mock_parcel)
        assert cost == Decimal('760.00')

    def test_calculate_cost_clothes(self):
        mock_parcel = MagicMock()
        mock_parcel.weight = Decimal('0.5')
        mock_parcel.content_value = Decimal('2000')
        mock_parcel.parcel_type.name = 'Одежда'

        cost = calculate_delivery_cost(mock_parcel)
        assert cost == Decimal('237.50')

    def test_calculate_cost_other(self):
        mock_parcel = MagicMock()
        mock_parcel.weight = Decimal('1.0')
        mock_parcel.content_value = Decimal('500')
        mock_parcel.parcel_type.name = 'Разное'

        cost = calculate_delivery_cost(mock_parcel)
        assert cost == Decimal('175.00')

    def test_calculate_cost_default_coefficient(self):
        """Тест расчета стоимости для неизвестного типа (коэффициент 1.0)"""
        mock_parcel = MagicMock()
        mock_parcel.weight = Decimal('2.0')
        mock_parcel.content_value = Decimal('1000')
        mock_parcel.parcel_type.name = 'Неизвестный тип'

        cost = calculate_delivery_cost(mock_parcel)
        assert cost == Decimal('250.00')


@pytest.mark.django_db
class TestCeleryTasks:
    """Тесты Celery задач с моками"""

    @patch('delivery.tasks.currency_service')
    @patch('delivery.tasks.Parcel')
    def test_calculate_single_parcel_success(self, MockParcel, mock_currency):
        """Тест успешного расчета для одной посылки"""
        mock_currency.get_usd_rate.return_value = Decimal('75.0')

        mock_parcel = Mock()
        mock_parcel.id = 1
        mock_parcel.name = 'Ноутбук'
        mock_parcel.weight = Decimal('2.0')
        mock_parcel.content_value = Decimal('10000')
        mock_parcel.parcel_type.name = 'Электроника'
        mock_parcel.delivery_cost = None

        MockParcel.objects.get.return_value = mock_parcel

        from delivery.tasks import calculate_parcel_delivery_cost
        result = calculate_parcel_delivery_cost(1)

        assert result['status'] == 'success'
        assert result['parcel_id'] == 1
        mock_parcel.save.assert_called_once_with(update_fields=['delivery_cost'])

    @patch('delivery.tasks.currency_service')
    def test_calculate_single_parcel_not_found(self, mock_currency):
        """Тест расчета для несуществующей посылки"""
        mock_currency.get_usd_rate.return_value = Decimal('75.0')

        from delivery.tasks import calculate_parcel_delivery_cost

        # Вызываем с несуществующим ID
        result = calculate_parcel_delivery_cost(99999)

        # Проверяем результат
        assert result['status'] == 'error'
        assert 'Parcel not found' in result['error']

    @patch('delivery.tasks.currency_service')
    @patch('delivery.tasks.calculate_parcel_delivery_cost')
    @patch('delivery.tasks.Parcel')
    def test_calculate_all_parcels(self, MockParcel, mock_calculate_single, mock_currency):
        """Тест расчета для всех посылок"""
        mock_currency.get_usd_rate.return_value = Decimal('75.0')

        mock_parcels = [
            Mock(id=1, delivery_cost=None),
            Mock(id=2, delivery_cost=None),
            Mock(id=3, delivery_cost=None)
        ]

        mock_queryset = Mock()
        mock_queryset.__iter__ = Mock(return_value=iter(mock_parcels))
        mock_queryset.filter.return_value = mock_queryset
        mock_queryset.count.return_value = 3

        MockParcel.objects.filter.return_value = mock_queryset

        mock_calculate_single.side_effect = [
            {'status': 'success', 'parcel_id': 1, 'delivery_cost': '760.00'},
            {'status': 'success', 'parcel_id': 2, 'delivery_cost': '237.50'},
            {'status': 'success', 'parcel_id': 3, 'delivery_cost': '175.00'}
        ]

        from delivery.tasks import calculate_all_parcels_delivery_cost
        result = calculate_all_parcels_delivery_cost()

        assert result['total'] == 3
        assert result['success'] == 3
        assert result['failed'] == 0

    @patch('delivery.tasks.currency_service')
    @patch('delivery.tasks.Parcel')
    def test_calculate_all_parcels_empty(self, MockParcel, mock_currency):
        """Тест расчета когда нет посылок без стоимости"""
        mock_currency.get_usd_rate.return_value = Decimal('75.0')

        mock_queryset = Mock()
        mock_queryset.__iter__ = Mock(return_value=iter([]))
        mock_queryset.filter.return_value = mock_queryset
        mock_queryset.count.return_value = 0

        MockParcel.objects.filter.return_value = mock_queryset

        from delivery.tasks import calculate_all_parcels_delivery_cost
        result = calculate_all_parcels_delivery_cost()

        assert result['total'] == 0
        assert result['success'] == 0
        assert result['failed'] == 0
#hi
