from unittest.mock import MagicMock

from delivery.utils import SessionManager


class TestSessionManager:
    """Unit тесты для SessionManager (без БД)"""

    def test_get_session_id_creates_new(self):
        """Тест создания новой сессии, если её нет"""
        # Создаем мок для сессии
        mock_session = MagicMock()
        mock_session.session_key = None

        # Функция, которая симулирует создание сессии
        def mock_create():
            mock_session.session_key = "newly_created_session_key_123"

        mock_session.create.side_effect = mock_create

        # Создаем мок для request
        mock_request = MagicMock()
        mock_request.session = mock_session

        # Вызываем метод
        session_id = SessionManager.get_session_id(mock_request)

        # Проверяем, что create был вызван
        mock_session.create.assert_called_once()

        # Проверяем, что session_key был установлен и возвращен
        assert session_id == "newly_created_session_key_123"
        assert mock_session.session_key == "newly_created_session_key_123"

    def test_get_session_id_returns_existing(self):
        """Тест возврата существующей сессии"""
        # Создаем мок для сессии с существующим ключом
        existing_key = "test_session_key_12345"
        mock_session = MagicMock()
        mock_session.session_key = existing_key

        # Создаем мок для request
        mock_request = MagicMock()
        mock_request.session = mock_session

        # Вызываем метод
        session_id = SessionManager.get_session_id(mock_request)

        # Проверяем, что create НЕ вызывался
        mock_session.create.assert_not_called()

        # Проверяем, что вернулся правильный ключ
        assert session_id == existing_key
#hi
