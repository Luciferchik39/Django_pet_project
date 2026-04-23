from unittest.mock import Mock

from delivery.exceptions import CurrencyRateError, ParcelNotFoundError, SessionError
import pytest


class TestExceptions:
    """Тесты для кастомных исключений"""

    def test_parcel_not_found_error(self):
        """Тест исключения ParcelNotFoundError"""
        error_message = "Посылка не найдена"

        with pytest.raises(ParcelNotFoundError) as exc_info:
            raise ParcelNotFoundError(error_message)

        assert str(exc_info.value) == error_message
        assert exc_info.value.__class__.__name__ == "ParcelNotFoundError"

    def test_currency_rate_error(self):
        """Тест исключения CurrencyRateError"""
        error_message = "Ошибка получения курса"

        with pytest.raises(CurrencyRateError) as exc_info:
            raise CurrencyRateError(error_message)

        assert str(exc_info.value) == error_message
        assert exc_info.value.__class__.__name__ == "CurrencyRateError"

    def test_session_error(self):
        """Тест исключения SessionError"""
        error_message = "Ошибка сессии"

        with pytest.raises(SessionError) as exc_info:
            raise SessionError(error_message)

        assert str(exc_info.value) == error_message
        assert exc_info.value.__class__.__name__ == "SessionError"

    def test_exceptions_inherit_from_base_exception(self):
        """Тест, что исключения наследуются от Exception"""
        assert issubclass(ParcelNotFoundError, Exception)
        assert issubclass(CurrencyRateError, Exception)
        assert issubclass(SessionError, Exception)

    def test_exception_with_mock(self):
        """Тест использования исключения с моком"""
        mock_error = Mock(spec=CurrencyRateError)
        mock_error.message = "Mocked error"

        with pytest.raises(CurrencyRateError):
            raise CurrencyRateError(str(mock_error.message))
