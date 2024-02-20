from django.urls import path
from .views import approve_booking

urlpatterns = [
    path('view/<str:booking_id>/approve/', approve_booking, name='approve-booking'),
]