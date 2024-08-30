from django.urls import path
from . import views
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

    path('billing/', views.billing_information_list, name='billing_information_list'),
    path('billing/add/', views.billing_information_create, name='billing_information_create'),
    path('billing/<int:pk>/', views.billing_information_detail ,name='billing_information_detail'),
    path('billing/<int:pk>/edit/', views.billing_information_update, name='billing_information_update'),
    path('billing/<int:pk>/delete/', views.billing_information_delete, name='billing_information_delete'),
]
