from django.urls import path
from . import routes
from . import api
from flightdesk.views import basic, dashboard, revision, chat
from django.shortcuts import redirect

def redirect_to_login(request):
    return redirect('login')

urlpatterns = [
    # Base
    path('', redirect_to_login, name='root'),

    # Authentication Routes
    path('login/', routes.login_view, name='login'),
    path('logout/', routes.logout_view, name='logout'),

    # Dashboard Routes
    path('dashboard/', routes.dashboard, name='dashboard'),
    path('api/call-log-summary/', api.call_log_summary_api, name='call_log_summary_api'),
    path('api/call-log-chart/', api.call_log_chart_api, name='call_log_chart_api'),
    path('api/booking-summary/', api.booking_summary_api, name='booking_summary_api'),
    path('api/call-log/download/', dashboard.download_call_log_excel, name='download_call_log_excel'),
    path('api/bookings/download/', dashboard.download_bookings_excel, name='download_bookings_excel'),


    # Staff Routes
    path('staff/create/', routes.staff_create, name='staff_create'),
    path('staff/', routes.staff_list, name='staff_list'),

    # CallLog Routes
    path('call_logs/', routes.call_log_list, name='call_log_list'),
    path('call_logs/add/', routes.call_log_create, name='call_log_add'),
    path('call_logs/<int:pk>/', routes.call_log_detail, name='call_log_detail'),
    path('call_logs/<int:pk>/edit/', routes.call_log_update, name='call_log_edit'),
    path('call_logs/<int:pk>/delete/', routes.call_log_delete, name='call_log_delete'),

    # Baisc Routes (for supervisor)
    path('campaigns/', routes.campaign_list, name='campaign_list'),
    path('campaigns/add/', routes.campaign_create, name='campaign_add'),
    path('campaigns/<int:id>/', routes.campaign_detail, name='campaign_detail'),
    path('campaigns/<int:id>/edit/', routes.campaign_update, name='campaign_edit'),
    path('campaigns/<int:id>/delete/', routes.campaign_delete, name='campaign_delete'),

    path('queries/', routes.query_list, name='query_list'),
    path('queries/create/', routes.query_create, name='query_create'),
    path('queries/<int:pk>/', routes.query_detail, name='query_detail'),
    path('queries/<int:pk>/update/', routes.query_update, name='query_update'),
    path('queries/<int:pk>/delete/', routes.query_delete, name='query_delete'),

    path('airlines/', basic.airline_list, name='airline_list'),
    path('airlines/add/', basic.airline_create, name='airline_add'),
    path('airlines/<int:pk>/', basic.airline_detail, name='airline_detail'),
    path('airlines/<int:pk>/edit/', basic.airline_update, name='airline_edit'),
    path('airlines/<int:pk>/delete/', basic.airline_delete, name='airline_delete'),    

    # Other Routes
    path('billing/', routes.billing_information_list, name='billing_information_list'),
    path('payment/<str:booking_id>/', routes.payment_done, name='payment_done'),
    path('billing/add/', routes.billing_information_create, name='billing_information_create'),
    path('billing/<int:pk>/', routes.billing_information_detail ,name='billing_information_detail'),
    path('billing/<int:pk>/edit/', routes.billing_information_update, name='billing_information_update'),
    path('billing/<int:pk>/delete/', routes.billing_information_delete, name='billing_information_delete'),

    path('bookings/', routes.booking_list, name='booking_list'),
    path('bookings/<int:pk>/', routes.booking_detail, name='booking_detail'),
    path('bookings/<int:pk>/edit/', routes.booking_edit, name='booking_edit'),
    path('booking/delete/<int:pk>/', routes.booking_delete, name='booking_delete'),
    path('bookings/<int:booking_pk>/add-billing-info/', routes.billing_info, name='billing_info'),

    path('api/search-customers/', api.search_customers, name='search_customers'),
    path('api/create-booking/', api.create_booking, name='create_booking'),
    path('api/add-billing-info/', api.add_billing_info, name='add_billing_info'),
    path('api/add-passengers/', api.add_passengers, name='add_passengers'),

    path('emails/', routes.email_list, name='email_list'),
    path('emails/c/<str:booking_id>/', routes.create_email, name='create_email'),
    path('emails/create/<str:booking_id>/', routes.email_create, name='email_create'),
    path('emails/<int:pk>/edit/', routes.email_edit, name='email_edit'),
    path('emails/<int:pk>/view/', routes.email_view, name='email_view'),
    path('emails/<int:pk>/delete/', routes.email_delete, name='email_delete'),
    path('emails/<int:pk>/send/', routes.email_send, name='email_send'),
    path('api/save-booking/', api.save_booking, name='save_booking'),

    path('approve/<str:booking_id>/', routes.approve_booking, name='approve_booking'),

    # Revision Routes
    path('revision/', revision.revision_list, name='revision_list'),  # Show revisions
    path('revision/<int:id>/edit/', revision.revision_edit, name='revision_edit'),  # Edit revision notes

    # Chat Routes
    path('chat/private/<int:user_id>/', chat.private_chat, name='private_chat'),
    path('chat/', chat.private_chat, name='private_chat_list'),
    path('chat/check_for_messages/', chat.check_for_messages, name='check_for_messages'),

]
