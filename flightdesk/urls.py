from django.urls import path
from .views import BookingApprovalView, SaveImageView
from .admin import BookingAdmin

urlpatterns = [
    path('booking/approval/<int:booking_id>/', BookingApprovalView.as_view(), name='booking_approval'),
    path('save_ticket_image/', SaveImageView.as_view(), name='admin_save_ticket_image'),
]