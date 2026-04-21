# apps/delivery/views.py (добавить новый класс)
from typing import List, Dict, Any
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request
from .serializers import ParcelCreateSerializer, ParcelResponseSerializer, ParcelTypeSerializer
from .utils import SessionManager
from .models import ParcelType, Parcel


class ParcelTypeListAPIView(APIView):
    """API для получения списка типов посылок"""

    def get(self, request: Request) -> Response:
        """
        GET /api/parcel-types/

        Ответ: список типов посылок
        """
        parcel_types = ParcelType.objects.all()
        serializer = ParcelTypeSerializer(parcel_types, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CreateParcelAPIView(APIView):
    """API для создания посылки"""

    def post(self, request: Request) -> Response:
        """POST /api/parcels/create/"""
        # Получаем ID сессии текущего пользователя
        session_id = SessionManager.get_session_id(request)

        # Валидируем данные
        serializer = ParcelCreateSerializer(
            data=request.data,
            context={'session_id': session_id}
        )

        if serializer.is_valid():
            # Сохраняем посылку
            parcel = serializer.save()

            return Response({
                'id': parcel.id,
                'message': 'Посылка успешно создана'
            }, status=status.HTTP_201_CREATED)

        # Возвращаем ошибки валидации
        return Response({
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ParcelDetailAPIView(APIView):
    """API для получения деталей посылки"""

    def get(self, request: Request, parcel_id: int) -> Response:
        """GET /api/parcels/{id}/"""
        session_id = SessionManager.get_session_id(request)

        try:
            parcel = Parcel.objects.get(id=parcel_id, session_id=session_id)
            serializer = ParcelResponseSerializer(parcel)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Parcel.DoesNotExist:
            return Response({
                'error': 'Посылка не найдена'
            }, status=status.HTTP_404_NOT_FOUND)


class UserParcelsAPIView(APIView):
    """API для получения всех посылок пользователя с пагинацией и фильтрацией"""

    def get(self, request: Request) -> Response:
        """
        GET /api/parcels/

        Параметры:
        - page: номер страницы (по умолчанию 1)
        - page_size: размер страницы (по умолчанию 10, максимум 100)
        - parcel_type: ID типа посылки (опционально)
        - delivery_cost_isnull: true/false (опционально)
        """
        session_id = SessionManager.get_session_id(request)

        # Базовый queryset
        parcels = Parcel.objects.filter(session_id=session_id)

        # Применяем фильтры
        parcel_type_id = request.query_params.get('parcel_type')
        if parcel_type_id and parcel_type_id.isdigit():
            parcels = parcels.filter(parcel_type_id=int(parcel_type_id))

        delivery_cost_isnull = request.query_params.get('delivery_cost_isnull')
        if delivery_cost_isnull is not None:
            if delivery_cost_isnull.lower() == 'true':
                parcels = parcels.filter(delivery_cost__isnull=True)
            elif delivery_cost_isnull.lower() == 'false':
                parcels = parcels.filter(delivery_cost__isnull=False)

        # Пагинация
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))

        # Ограничиваем page_size
        if page_size > 100:
            page_size = 100
        if page_size < 1:
            page_size = 10

        # Вычисляем offset и limit
        offset = (page - 1) * page_size
        total_count = parcels.count()

        # Получаем посылки для текущей страницы
        parcels_page = parcels[offset:offset + page_size]

        # Сериализуем
        serializer = ParcelResponseSerializer(parcels_page, many=True)

        # Формируем ответ с мета-информацией
        return Response({
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size if total_count > 0 else 1,
            'results': serializer.data
        }, status=status.HTTP_200_OK)