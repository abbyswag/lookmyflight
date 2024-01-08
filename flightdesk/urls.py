from django.urls import path
from .views import approve_booking

urlpatterns = [
    path('bid/<str:bid_id>/approve/', approve_booking, name='approve-booking'),
]