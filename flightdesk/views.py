# from django.shortcuts import render, get_object_or_404
# from django.contrib import messages 
# from .models import Booking


# def approve_booking(request, booking_id):
#   booking = get_object_or_404(Booking, booking_id=booking_id)
#   booking.status = 'allocating'
#   booking.save()
#   messages.success(request, 'Booking approved.')
#   return render(request, 'approved.html', {
#     'mybooking_id': booking_id
#   })

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import CallLog, Campaign
from .forms import CallLogForm, CampaignForm
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import TruncDate

# Authentication Views
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'crm/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

# Dashboard View
@login_required
def dashboard(request):
    is_supervisor = request.user.groups.filter(name='supervisor').exists()

    # Default filter: Total calls by date
    filter_type = request.GET.get('filter', 'total')
    labels, data = '', ''
    today = timezone.now().date()
    start_date = today - timedelta(days=30)  # Last 30 days
    queryset = CallLog.objects.filter(call_date__date__gte=start_date)

    if filter_type == 'tags':
        chart_data = queryset.values('tag__code').annotate(call_count=Count('id')).order_by('tag__code')
        labels = [entry['tag__code'] for entry in chart_data]
        data = [entry['call_count'] for entry in chart_data]
    elif filter_type == 'conversion':
        chart_data = queryset.values('converted').annotate(call_count=Count('id')).order_by('converted')
        labels = [entry['converted'] for entry in chart_data]
        data = [entry['call_count'] for entry in chart_data]
    else:
        queryset = CallLog.objects.all()
        chart_data = queryset.annotate(
            date_only=TruncDate('call_date')
        ).values('date_only').annotate(
            call_count=Count('id')
        ).order_by('date_only')
        
        labels = [entry['date_only'].strftime('%Y-%m-%d') for entry in chart_data]
        data = [entry['call_count'] for entry in chart_data]

    context = {
        'is_supervisor': is_supervisor,
        'labels': labels,
        'data': data,
        'filter_type': filter_type,
    }
    print(context['data'][0])
    return render(request, 'crm/dashboard.html', context)

# Check for Supervisor Group
def is_supervisor(user):
    return user.groups.filter(name='supervisor').exists()

from django.db.models import Q
from django.contrib.auth.models import User

# CallLog Views
@login_required
def call_log_list(request):
    user = request.user
    is_supervisor = user.groups.filter(name='Supervisor').exists()
    
    # Initialize filter parameters
    date = request.GET.get('date', None)
    tag = request.GET.get('tag', None)
    conversion = request.GET.get('conversion', None)
    added_by = request.GET.get('added_by', None)
    
    filters = Q()
    
    if date:
        filters &= Q(call_date__date=date)
    if tag:
        filters &= Q(tag__code=tag)
    if conversion:
        filters &= Q(converted=conversion)
    if added_by and is_supervisor:
        filters &= Q(added_by__username=added_by)

    call_logs = CallLog.objects.filter(filters).select_related('tag', 'added_by')
    
    # Prepare for the dropdown filters
    tags = Campaign.objects.all()
    users = User.objects.all()
    
    context = {
        'call_logs': call_logs,
        'tags': tags,
        'users': users,
        'selected_date': date,
        'selected_tag': tag,
        'selected_conversion': conversion,
        'selected_added_by': added_by,
        'is_supervisor': is_supervisor,
    }
    
    return render(request, 'crm/call_log_list.html', context)

@login_required
def call_log_create(request):
    if request.method == 'POST':
        form = CallLogForm(request.POST)
        if form.is_valid():
            call_log = form.save(commit=False)
            call_log.added_by = request.user
            call_log.save()
            return redirect('call_log_list')
    else:
        form = CallLogForm()
    return render(request, 'crm/call_log_form.html', {'form': form})

@login_required
def call_log_detail(request, pk):
    call_log = get_object_or_404(CallLog, pk=pk)
    return render(request, 'crm/call_log_detail.html', {'call_log': call_log})

@login_required
def call_log_update(request, pk):
    call_log = get_object_or_404(CallLog, pk=pk)
    if request.method == 'POST':
        form = CallLogForm(request.POST, instance=call_log)
        if form.is_valid():
            form.save()
            return redirect('call_log_detail', pk=pk)
    else:
        form = CallLogForm(instance=call_log)
    return render(request, 'crm/call_log_form.html', {'form': form})

@login_required
def call_log_delete(request, pk):
    call_log = get_object_or_404(CallLog, pk=pk)
    if request.method == 'POST':
        call_log.delete()
        return redirect('call_log_list')
    return render(request, 'crm/call_log_confirm_delete.html', {'call_log': call_log})

# Campaign Views (Supervisor only)
@login_required
@user_passes_test(is_supervisor)
def campaign_list(request):
    campaigns = Campaign.objects.all()
    return render(request, 'campaign_list.html', {'campaigns': campaigns})

@login_required
@user_passes_test(is_supervisor)
def campaign_create(request):
    if request.method == 'POST':
        form = CampaignForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('campaign_list')
    else:
        form = CampaignForm()
    return render(request, 'campaign_form.html', {'form': form})

@login_required
@user_passes_test(is_supervisor)
def campaign_detail(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)
    return render(request, 'campaign_detail.html', {'campaign': campaign})

@login_required
@user_passes_test(is_supervisor)
def campaign_update(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)
    if request.method == 'POST':
        form = CampaignForm(request.POST, instance=campaign)
        if form.is_valid():
            form.save()
            return redirect('campaign_detail', pk=pk)
    else:
        form = CampaignForm(instance=campaign)
    return render(request, 'crm/campaign_form.html', {'form': form})

@login_required
@user_passes_test(is_supervisor)
def campaign_delete(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)
    if request.method == 'POST':
        campaign.delete()
        return redirect('campaign_list')
    return render(request, 'crm/campaign_confirm_delete.html', {'campaign': campaign})

@login_required
@user_passes_test(is_supervisor)
def campaign_list(request):
    campaigns = Campaign.objects.all()
    return render(request, 'crm/campaign_list.html', {'campaigns': campaigns})

@login_required
@user_passes_test(is_supervisor)
def campaign_detail(request, id):
    campaign = get_object_or_404(Campaign, id=id)
    return render(request, 'crm/campaign_detail.html', {'campaign': campaign})

@login_required
@user_passes_test(is_supervisor)
def campaign_create(request):
    if request.method == 'POST':
        form = CampaignForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('campaign_list')
    else:
        form = CampaignForm()
    return render(request, 'crm/campaign_form.html', {'form': form, 'campaign': None})

@login_required
@user_passes_test(is_supervisor)
def campaign_update(request, id):
    campaign = get_object_or_404(Campaign, id=id)
    if request.method == 'POST':
        form = CampaignForm(request.POST, instance=campaign)
        if form.is_valid():
            form.save()
            return redirect('campaign_list')
    else:
        form = CampaignForm(instance=campaign)
    return render(request, 'crm/campaign_form.html', {'form': form, 'campaign': campaign})

@login_required
@user_passes_test(is_supervisor)
def campaign_delete(request, id):
    campaign = get_object_or_404(Campaign, id=id)
    if request.method == 'POST':
        campaign.delete()
        return redirect('campaign_list')
    return render(request, 'crm/campaign_confirm_delete.html', {'campaign': campaign})

