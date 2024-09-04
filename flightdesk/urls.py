from django.urls import path
from . import views
from . import api
from django.shortcuts import redirect

def redirect_to_login(request):
    return redirect('login')

urlpatterns = [
    path('', redirect_to_login, name='root'),

    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/call-log-summary/', api.call_log_summary_api, name='call_log_summary_api'),
    path('api/call-log-chart/', api.call_log_chart_api, name='call_log_chart_api'),
    path('api/booking-summary/', api.booking_summary_api, name='booking_summary_api'),


    # Staff
    path('staff/create/', views.staff_create, name='staff_create'),
    path('staff/', views.staff_list, name='staff_list'),

    # CallLog CRUD
    path('call_logs/', views.call_log_list, name='call_log_list'),
    path('call_logs/add/', views.call_log_create, name='call_log_add'),
    path('call_logs/<int:pk>/', views.call_log_detail, name='call_log_detail'),
    path('call_logs/<int:pk>/edit/', views.call_log_update, name='call_log_edit'),
    path('call_logs/<int:pk>/delete/', views.call_log_delete, name='call_log_delete'),

    # Campaign CRUD (for supervisor)
    path('campaigns/', views.campaign_list, name='campaign_list'),
    path('campaigns/add/', views.campaign_create, name='campaign_add'),
    path('campaigns/<int:id>/', views.campaign_detail, name='campaign_detail'),
    path('campaigns/<int:id>/edit/', views.campaign_update, name='campaign_edit'),
    path('campaigns/<int:id>/delete/', views.campaign_delete, name='campaign_delete'),

    path('queries/', views.query_list, name='query_list'),
    path('queries/create/', views.query_create, name='query_create'),
    path('queries/<int:pk>/', views.query_detail, name='query_detail'),
    path('queries/<int:pk>/update/', views.query_update, name='query_update'),
    path('queries/<int:pk>/delete/', views.query_delete, name='query_delete'),

    path('billing/', views.billing_information_list, name='billing_information_list'),
    path('payment/<str:booking_id>/', views.payment_done, name='payment_done'),
    path('billing/add/', views.billing_information_create, name='billing_information_create'),
    path('billing/<int:pk>/', views.billing_information_detail ,name='billing_information_detail'),
    path('billing/<int:pk>/edit/', views.billing_information_update, name='billing_information_update'),
    path('billing/<int:pk>/delete/', views.billing_information_delete, name='billing_information_delete'),

    path('bookings/', views.booking_list, name='booking_list'),
    path('bookings/<int:pk>/', views.booking_detail, name='booking_detail'),
    path('bookings/<int:pk>/edit/', views.booking_edit, name='booking_edit'),
    path('booking/delete/<int:pk>/', views.booking_delete, name='booking_delete'),
    path('bookings/<int:booking_pk>/add-billing-info/', views.billing_info, name='billing_info'),

    path('api/search-customers/', api.search_customers, name='search_customers'),
    path('api/create-booking/', api.create_booking, name='create_booking'),
    path('api/add-billing-info/', api.add_billing_info, name='add_billing_info'),
    path('api/add-passengers/', api.add_passengers, name='add_passengers'),

    path('emails/', views.email_list, name='email_list'),
    path('emails/c/<str:booking_id>/', views.create_email, name='create_email'),
    path('emails/create/<str:booking_id>/', views.email_create, name='email_create'),
    path('emails/<int:pk>/edit/', views.email_edit, name='email_edit'),
    path('emails/<int:pk>/view/', views.email_view, name='email_view'),
    path('emails/<int:pk>/delete/', views.email_delete, name='email_delete'),
    path('emails/<int:pk>/send/', views.email_send, name='email_send'),
    path('api/save-booking/', api.save_booking, name='save_booking'),

    path('approve/<str:booking_id>/', views.approve_booking, name='approve_booking'),

]
