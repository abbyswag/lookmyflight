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
            # Check group and redirect accordingly
            if user.groups.filter(name='agent').exists():
                return redirect('agent_dashboard')  # Redirect to the agent dashboard
            else:
                return redirect('dashboard')  # Redirect to the general dashboard
        else:
            return render(request, 'crm/login.html', {'error': 'Invalid credentials'})
    return render(request, 'crm/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')


# Check for Supervisor Group
def is_supervisor(user):
    return user.groups.filter(name='supervisor').exists()

from django.db.models import Q
from django.contrib.auth.models import User

@login_required
def dashboard(request):
    user = request.user
    is_supervisor = user.groups.filter(name='supervisor').exists()

    tags = Campaign.objects.all()
    query_types = Query.objects.all()

    context = {
        'is_supervisor': is_supervisor,
        'tags': tags,
        'query_types': query_types,
    }

    return render(request, 'crm/dashboard.html', context)

# Staff Views
@login_required
@user_passes_test(is_supervisor)
def staff_create(request):
    if request.method == 'POST':
        form = StaffCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('staff_list')
    else:
        form = StaffCreationForm()
    return render(request, 'crm/staff_form.html', {'form': form})

@login_required
@user_passes_test(is_supervisor)
def staff_list(request):
    staff = User.objects.filter(groups__name__in=['agent', 'supervisor', 'cs_team'])
    return render(request, 'crm/staff_list.html', {'staff': staff})


# Campaign Routes
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
    is_supervisor = user.groups.filter(name='supervisor').exists()
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
        'is_supervisor': is_supervisor,
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
        bookings = Booking.objects.filter(added_by=request.user).order_by('-created_at')
    else:
        bookings = Booking.objects.all().order_by('-created_at')
    return render(request, 'crm/booking_list.html', {'bookings': bookings, 'is_supervisor': is_supervisor(request.user)})

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
        'is_supervisor': is_supervisor(request.user),
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

from django.contrib import messages

@login_required
@user_passes_test(is_supervisor)
def payment_done(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id)
    
    # Check if the booking is in a state where payment can be made
    if booking.status == 'allocating':
        messages.error(request, "Invalid booking status for payment completion.")
        return redirect('booking_detail', pk=booking.pk)
    
    # Update the booking status to confirmed
    booking.status = 'confirmed'
    booking.save()
    
    messages.success(request, f"Payment for booking {booking_id} has been confirmed.")
    
    # Redirect back to the booking detail page
    return redirect('booking_detail', pk=booking.pk)

from django.http import HttpResponseForbidden

@login_required
def booking_delete(request, pk):
    booking= get_object_or_404(Booking, pk=pk)
    if request.method == 'POST':
        booking.delete()
        return redirect('booking_list')
    return render(request, 'crm/booking_confirm_delete.html', {'booking': booking})
    
# Email Model Routes
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Email

@login_required
def email_list(request):
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '').strip()

    # Fetch all emails
    emails = Email.objects.all().order_by('-id')

    # Apply search filter (by customer name)
    if search_query:
        emails = emails.filter(booking__call_log__name__icontains=search_query)

    # Apply status filter
    if status_filter in ['draft', 'sent']:
        emails = emails.filter(status=status_filter)

    # Pagination (100 emails per page)
    paginator = Paginator(emails, 100)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'crm/email_list.html', {'emails': page_obj})

@login_required
def create_email(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id)
    context = {
        'booking': booking
    }
    email_body = render_to_string('email_templates/conf.html', context)
    form = EmailForm(initial={
            'recipient': booking.call_log.email,
            'subject': f'Booking Confirmation: {booking.booking_id}',
            'body': email_body,
        })
    return render(request, 'crm/email_form.html', {'form': form, 'booking': booking})

@login_required
def email_create(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id)
    billing_info = BillingInformation.objects.filter(booking=booking)
    passenger_info = Passenger.objects.filter(booking = booking)
    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            email = form.save(commit=False)
            email.booking = booking
            email.save()
            return redirect('email_list')
    else:
        prefix = 'http://127.0.0.1:8000/'
        approval_url = prefix + f'/approve/{booking.booking_id}'
        total_amount = str(booking.mco + booking.flight_cost + booking.hotel_cost + booking.vehicle_cost)
        
        if '.' in total_amount:
            integer_part, decimal_part = total_amount.split('.')
            if len(decimal_part) == 1:
                total_amount = f"{integer_part}.{decimal_part}0"
        else:
            total_amount = f"{total_amount}.00"      

        context = {
            'booking': booking,
            'total_amount': total_amount,
            'billing_info': billing_info,
            'passenger_info':passenger_info,
            'approval_url': approval_url,
            'flight_info_img': prefix + booking.flight_info_img.url if booking.flight_info_img else None,
            'hotel_info_img': prefix + booking.hotel_info_img.url if booking.hotel_info_img else None,
            'vehicle_info_img': prefix + booking.vehicle_info_img.url if booking.vehicle_info_img else None,
        }
        email_body = render_to_string('email_templates/auth.html', context)

        form = EmailForm(initial={
            'recipient': booking.call_log.email,
            'subject': f'Booking Authorization: {booking.booking_id}',
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

        booking.status = 'authorizing'
        booking.save()

    except Exception as e:
        print(f"Error sending email: {e}")
    return redirect('email_list')

from bs4 import BeautifulSoup
def get_clened_email(booking):
    email = Email.objects.filter(booking=booking).first()
    email_body = email.body if email else 'No email found.'
    soup = BeautifulSoup(email_body, 'html.parser')
    
    # Remove all anchor (<a>) tags
    for a_tag in soup.find_all('a'):
        a_tag.decompose()
    
    cleaned_email_body = str(soup)
    return cleaned_email_body, email.recipient

from datetime import datetime
from django.http import JsonResponse


def approve_booking(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id)

    if request.method == 'POST':
        # 1. If staff is NOT filling billing (=> user must fill):
        if not booking.staff_fill_billing:
            # Check if we already have a BillingInformation record
            billing_exists = BillingInformation.objects.filter(booking=booking).exists()
            if not billing_exists:
                data = request.POST
                # Example basic validations (you can expand as needed or reuse your `add_billing_info` logic):
                required_fields = [
                    'card_type', 'card_holder_name', 'card_holder_number', 'email',
                    'card_number', 'expiry_date', 'card_cvv', 'primary_address',
                    'country', 'zipcode'
                ]
                for field in required_fields:
                    if field not in data or not data[field].strip():
                        return JsonResponse({'success': False, 'error': f"{field} is required and cannot be blank."})

                # Create the billing record
                BillingInformation.objects.create(
                    booking=booking,
                    card_type=data['card_type'],
                    card_holder_name=data['card_holder_name'],
                    card_holder_number=data['card_holder_number'],
                    email=data['email'],
                    card_number=data['card_number'],
                    expiry_date=data['expiry_date'],
                    card_cvv=data['card_cvv'],
                    primary_address=data['primary_address'],
                    country=data['country'],
                    zipcode=data['zipcode'],
                )

        # 2. In both cases (staff_fill_billing = True or False), handle final signature logic:
        booking.status = 'allocating'
        booking.save()

        # Retrieve the email body and recipient
        email_body, rec = get_clened_email(booking)

        # Extract form fields for signature
        full_name = request.POST.get('fullName')
        signature_style = request.POST.get('signatureStyle')

        # Build user declaration with date/time
        now = datetime.now()
        date_time_string = now.strftime('%B %d, %Y at %I:%M %p')
        user_declaration = f"""
            <hr>
            <p><strong style="color: green; text-align: center;">&#10004; I confirm that I have read and agreed to the above terms.</strong></p>
            <p style="text-align: left; color: gray">Dated: {date_time_string} UTC </p>
            <p style="text-align: right; font-family: {signature_style}, cursive; font-size: 24px;">{full_name}</p>
        """

        final_email_body = f"{email_body}{user_declaration}"

        # Create and save the email record
        new_email = Email(
            subject=f"Signed Document for Booking ID {booking.booking_id}",
            recipient=rec,
            body=final_email_body,
            status='sent',
            booking=booking
        )
        new_email.save()

        return render(request, 'approved.html', {'booking_id': booking.booking_id})

    else:
        # GET or other HTTP methods
        if booking.status == 'authorizing':
            # For the GET, show the 'authorizing' page
            email_body, _ = get_clened_email(booking)
            
            # If staff_fill_billing=False, user must see billing form
            # If staff_fill_billing=True, skip billing form
            show_billing = not booking.staff_fill_billing

            return render(request, 'authorizing_booking.html', {
                'booking_id': booking.booking_id,
                'email_body': email_body,
                'show_billing_form': show_billing,
            })
        
        # If not in authorizing status, user might have already signed or can't sign
        email_body, _ = get_clened_email(booking)
        return render(request, 'already_signed.html', {
            'email_body': email_body,
            'booking_id': booking.booking_id,
        })


from .models import Query
from .forms import QueryForm

# Query Views
@login_required
@user_passes_test(is_supervisor)
def query_list(request):
    queries = Query.objects.all()
    return render(request, 'crm/query_list.html', {'queries': queries})

@login_required
@user_passes_test(is_supervisor)
def query_create(request):
    if request.method == 'POST':
        form = QueryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('query_list')
    else:
        form = QueryForm()
    return render(request, 'crm/query_form.html', {'form': form})

@login_required
@user_passes_test(is_supervisor)
def query_detail(request, pk):
    query = get_object_or_404(Query, pk=pk)
    return render(request, 'crm/query_detail.html', {'query': query})

@login_required
@user_passes_test(is_supervisor)
def query_update(request, pk):
    query = get_object_or_404(Query, pk=pk)
    if request.method == 'POST':
        form = QueryForm(request.POST, instance=query)
        if form.is_valid():
            form.save()
            return redirect('query_detail', pk=pk)
    else:
        form = QueryForm(instance=query)
    return render(request, 'crm/query_form.html', {'form': form, 'query': query})

@login_required
@user_passes_test(is_supervisor)
def query_delete(request, pk):
    query = get_object_or_404(Query, pk=pk)
    if request.method == 'POST':
        query.delete()
        return redirect('query_list')
    return render(request, 'crm/query_confirm_delete.html', {'query': query})
