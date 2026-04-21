# apps/delivery/urls.py
from django.urls import path
from .views import (
    CreateParcelAPIView,
    ParcelDetailAPIView,
    UserParcelsAPIView,
    ParcelTypeListAPIView
)

app_name = 'delivery'

urlpatterns = [
    # Типы посылок
    path('api/parcel-types/', ParcelTypeListAPIView.as_view(), name='parcel-types'),

    # Посылки
    path('api/parcels/', UserParcelsAPIView.as_view(), name='parcels-list'),
    path('api/parcels/create/', CreateParcelAPIView.as_view(), name='parcel-create'),
    path('api/parcels/<int:parcel_id>/', ParcelDetailAPIView.as_view(), name='parcel-detail'),
]