from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import CallLog, Campaign, BillingInformation, Booking, Passenger, Email
from .forms import CallLogForm, CampaignForm, BillingInformationForm, StaffCreationForm, BookingForm, EmailForm
from django.db.models import Count
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta
from django.template.loader import render_to_string
from django.db.models.functions import TruncDate
from django.utils.html import format_html

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
    return render(request, 'crm/dashboard.html', context)

# Check for Supervisor Group
def is_supervisor(user):
    return user.groups.filter(name='supervisor').exists()

from django.db.models import Q
from django.contrib.auth.models import User


# Staff Views
@login_required
@user_passes_test(is_supervisor)
def staff_create(request):
    if request.method == 'POST':
        form = StaffCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('staff_list')  # Redirect to a list of staff members
    else:
        form = StaffCreationForm()
    return render(request, 'crm/staff_form.html', {'form': form})

@login_required
@user_passes_test(is_supervisor)
def staff_list(request):
    staff = User.objects.filter(groups__name__in=['agent', 'supervisor'])
    return render(request, 'crm/staff_list.html', {'staff': staff})



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


# Utility functions
def is_supervisor(user):
    return user.groups.filter(name='supervisor').exists()

def is_agent(user):
    return user.groups.filter(name='agent').exists()

# Billing Information List View
@login_required
def billing_information_list(request):
    user = request.user
    is_supervisor = user.groups.filter(name='Supervisor').exists()
    
    if is_supervisor:
        billing_infos = BillingInformation.objects.all()
    else:
        billing_infos = BillingInformation.objects.filter(added_by=user)
    
    # Hide sensitive information for agents
    if is_agent(user):
        for billing_info in billing_infos:
            billing_info.card_number = billing_info.card_number[:4] + "****" * 2 + billing_info.card_number[-4:]
            billing_info.card_cvv = "****"
            billing_info.expiry_date = "****"
    
    context = {
        'billing_infos': billing_infos,
        'is_supervisor': is_supervisor,
    }
    return render(request, 'crm/billing_information_list.html', context)

# Billing Information Create View
@login_required
@user_passes_test(is_agent)
def billing_information_create(request):
    if request.method == 'POST':
        form = BillingInformationForm(request.POST)
        if form.is_valid():
            billing_info = form.save(commit=False)
            billing_info.added_by = request.user
            billing_info.save()
            return redirect('billing_information_list')
    else:
        form = BillingInformationForm()
    return render(request, 'crm/billing_information_form.html', {'form': form})

# Billing Information Detail View
@login_required
def billing_information_detail(request, pk):
    billing_info = get_object_or_404(BillingInformation, pk=pk)
    user = request.user
    
    if is_agent(user) and billing_info.added_by != user:
        return redirect('billing_information_list')  # Agents can't view others' billing info
    
    # Hide sensitive information for agents
    if is_agent(user):
        billing_info.card_number = billing_info.card_number[:4] + "****" * 2 + billing_info.card_number[-4:]
        billing_info.card_cvv = "****"
        billing_info.expiry_date = "****"
    
    context = {
        'billing_info': billing_info,
        'is_supervisor': is_supervisor(user),
    }
    return render(request, 'crm/billing_information_detail.html', context)

# Billing Information Update View
@login_required
@user_passes_test(is_supervisor)
def billing_information_update(request, pk):
    billing_info = get_object_or_404(BillingInformation, pk=pk)
    if request.method == 'POST':
        form = BillingInformationForm(request.POST, instance=billing_info)
        if form.is_valid():
            form.save()
            return redirect('billing_information_detail', pk=pk)
    else:
        form = BillingInformationForm(instance=billing_info)
    return render(request, 'crm/billing_information_form.html', {'form': form})

# Billing Information Delete View
@login_required
@user_passes_test(is_supervisor)
def billing_information_delete(request, pk):
    billing_info = get_object_or_404(BillingInformation, pk=pk)
    if request.method == 'POST':
        billing_info.delete()
        return redirect('billing_information_list')
    return render(request, 'crm/billing_information_confirm_delete.html', {'billing_info': billing_info})


@login_required
def booking_list(request):
    if is_agent(request.user):
        bookings = Booking.objects.filter(added_by=request.user)
    else:
        bookings = Booking.objects.all()
    return render(request, 'crm/booking_list.html', {'bookings': bookings})

@login_required
def booking_detail(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if is_agent(request.user) and booking.added_by != request.user:
        return redirect('booking_list')

    passengers = Passenger.objects.filter(booking=booking)
    billing_infos = BillingInformation.objects.filter(booking=booking)
    emails = Email.objects.filter(booking=booking) 
    
    context = {
        'booking': booking,
        'passengers': passengers,
        'billing_infos': billing_infos,
        'emails': emails, 
        'is_agent': is_agent(request.user),
    }
    return render(request, 'crm/booking_detail.html', context)

@login_required
def booking_edit(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if is_agent(request.user) and booking.added_by != request.user:
        return redirect('booking_list')

    if request.method == 'POST':
        form = BookingForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            return redirect('booking_detail', pk=booking.pk)
    else:
        form = BookingForm(instance=booking)

    passengers = Passenger.objects.filter(booking=booking)
    billing_infos = BillingInformation.objects.filter(booking=booking)
    
    context = {
        'form': form,
        'booking': booking,
        'passengers': passengers,
        'billing_infos': billing_infos,
        'is_agent': is_agent(request.user),
    }
    return render(request, 'crm/booking_edit.html', context)

@login_required
def billing_info(request, booking_pk):
    booking = get_object_or_404(Booking, pk=booking_pk)
    
    if request.method == 'POST':
        form = BillingInformationForm(request.POST)
        if form.is_valid():
            billing_info = form.save(commit=False)
            billing_info.booking = booking
            billing_info.save()
            return redirect(reverse('booking_detail', args=[booking.pk]))
        else:
            print(form.errors)
    else:
        form = BillingInformationForm()

    return render(request, 'crm/add_billing_info.html', {'form': form, 'booking': booking})

from django.http import HttpResponseForbidden

@login_required
def booking_delete(request, pk):
    booking= get_object_or_404(Booking, pk=pk)
    if request.method == 'POST':
        booking.delete()
        return redirect('booking_list')
    return render(request, 'crm/booking_confirm_delete.html', {'booking': booking})
    
# Email Model Routes
@login_required
def email_list(request):
    emails = Email.objects.all()
    if request.user.groups.filter(name='agent').exists():
        emails = Email.objects.filter(booking__added_by=request.user)
    return render(request, 'crm/email_list.html', {'emails': emails})

@login_required
def create_email(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id)
    if booking.status != 'allocating':
        return HttpResponseForbidden("Booking must be approved to send an email.")
    
    form = EmailForm(initial={
            'recipient': booking.call_log.email,
            'subject': f'Booking Confirmation: {booking.booking_id}',
        })
    return render(request, 'crm/email_form.html', {'form': form, 'booking': booking})

@login_required
def email_create(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id)
    billing_info = BillingInformation.objects.filter(booking=booking)
    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            email = form.save(commit=False)
            email.booking = booking
            email.save()
            return redirect('email_list')
    else:
        approval_url = request.build_absolute_uri(reverse('approve_booking', args=[booking.booking_id]))

        context = {
            'booking': booking,
            'billing_info': billing_info,
            'approval_url': approval_url,
            'flight_info_img': booking.flight_info_img.url if booking.flight_info_img else None,
            'hotel_info_img': booking.hotel_info_img.url if booking.hotel_info_img else None,
            'vehicle_info_img': booking.vehicle_info_img.url if booking.vehicle_info_img else None,
        }
        email_body = render_to_string('email_templates/auth.html', context)

        form = EmailForm(initial={
            'recipient': booking.call_log.email,
            'subject': f'Booking Initialization: {booking.booking_id}',
            'body': email_body
        })
        if form.is_valid():
            email = form.save(commit=False)
            email.booking = booking
            email.save()
            return redirect('email_list')
    return render(request, 'crm/email_form.html', {'form': form, 'booking': booking})

@login_required
def email_edit(request, pk):
    email = get_object_or_404(Email, pk=pk)
    if request.method == 'POST':
        form = EmailForm(request.POST, instance=email)
        if form.is_valid():
            form.save()
            return redirect('email_list')
    else:
        form = EmailForm(instance=email)
    return render(request, 'crm/email_form.html', {'form': form, 'email': email})

@login_required
def email_view(request, pk):
    email = get_object_or_404(Email, pk=pk)
    return render(request, 'crm/email_view.html', {'email': email})

@login_required
@user_passes_test(is_supervisor)
def email_delete(request, pk):
    email = get_object_or_404(Email, pk=pk)
    if request.method == 'POST':
        email.delete()
        return redirect('email_list')
    return render(request, 'crm/email_confirm_delete.html', {'email': email})

from django.core.mail import EmailMessage
from django.conf import settings

@login_required
def email_send(request, pk):
    email = get_object_or_404(Email, pk=pk)
    booking = email.booking

    try:
        # Create and send the email
        msg = EmailMessage(
            subject=email.subject,
            body=email.body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email.recipient]
        )
        msg.content_subtype = "html" 
        msg.send()

        email.status = 'sent'
        email.save()
    except Exception as e:
        print(f"Error sending email: {e}")
    return redirect('email_list')


@login_required
def approve_booking(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id)
    
    # Update the status of the booking to 'approved'
    booking.status = 'allocating'
    booking.save()
    
    # Redirect to a confirmation page or a list page
    return redirect('booking_approved', booking_id=booking.booking_id)
    
