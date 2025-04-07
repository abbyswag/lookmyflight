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
from django.core.mail import EmailMessage
from django.conf import settings
import threading
from django.contrib import messages
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

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
        # prefix = 'http://localhost:8000'
        prefix = 'http://35.182.117.59:8000'
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

from bs4 import BeautifulSoup
def get_clened_email(booking):
    email = Email.objects.filter(booking=booking).first()
    email_body = email.body if email else 'No email found.'
    soup = BeautifulSoup(email_body, 'html.parser')
    
    # Remove all anchor (<a>) tags
    for a_tag in soup.find_all('a'):
        a_tag.decompose()
    
    # For approval page: Hide the Card Details section
    # Look for the Card Details section and remove it
    card_details_heading = soup.find('h2', text='Card Details', class_='highlited')
    if card_details_heading:
        # Find the parent div that contains the entire card details section
        parent_div = card_details_heading.find_parent('div')
        if parent_div:
            parent_div.decompose()
    
    cleaned_email_body = str(soup)
    return cleaned_email_body, email.recipient

from datetime import datetime
from django.http import JsonResponse

# Separated email creation function
def create_signed_email_in_background(booking_id, full_name, signature_style):
    # Get booking and related data
    booking = Booking.objects.get(booking_id=booking_id)
    billing_info = BillingInformation.objects.filter(booking=booking)
    passenger_info = Passenger.objects.filter(booking=booking)
    
    # Get the same prefix and other settings
    # prefix = 'http://localhost:8000'
    prefix = 'http://35.182.117.59:8000'
    # approval_url = prefix + f'/approve/{booking.booking_id}'
    total_amount = str(booking.mco + booking.flight_cost + booking.hotel_cost + booking.vehicle_cost)
    
    if '.' in total_amount:
        integer_part, decimal_part = total_amount.split('.')
        if len(decimal_part) == 1:
            total_amount = f"{integer_part}.{decimal_part}0"
    else:
        total_amount = f"{total_amount}.00"
        
    # Regenerate the email body
    context = {
        'booking': booking,
        'total_amount': total_amount,
        'billing_info': billing_info,
        'passenger_info': passenger_info,
        'approval_url': None,
        'flight_info_img': prefix + booking.flight_info_img.url if booking.flight_info_img else None,
        'hotel_info_img': prefix + booking.hotel_info_img.url if booking.hotel_info_img else None,
        'vehicle_info_img': prefix + booking.vehicle_info_img.url if booking.vehicle_info_img else None,
    }
    
    # Generate the complete email body
    email_body = render_to_string('email_templates/auth.html', context)

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

    try:
        # Create and save the email record with the complete information
        new_email = Email(
            subject=f"Signed Document for Booking ID {booking.booking_id}",
            recipient=booking.call_log.email,
            body=final_email_body,
            status='sent',
            booking=booking
        )
        new_email.save()
        print(f"[INFO] Signed email created successfully for booking {booking_id}")
    except Exception as e:
        print(f"[ERROR] Failed to create signed email for booking {booking_id}: {str(e)}")

def approve_booking(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id)

    if request.method == 'POST':
        # 1. If staff is NOT filling billing (=> user must fill card details):
        if not booking.staff_fill_billing:
            try:
                # Check if we already have a BillingInformation record
                billing_info = BillingInformation.objects.get(booking=booking)
                
                # Check if we need to update card information (look for placeholders)
                if billing_info.card_number == '0000000000000000' or billing_info.card_type == 'Pending':
                    data = request.POST
                    # Validate card information (only what the customer provides)
                    required_fields = [
                        'card_type', 'card_holder_name', 'card_number', 
                        'expiry_date', 'card_cvv'
                    ]
                    for field in required_fields:
                        if field not in data or not data[field].strip():
                            return JsonResponse({'success': False, 'error': f"{field.replace('_', ' ').capitalize()} is required and cannot be blank."})
                    
                    # Update only the card fields, keeping the address information
                    # and existing contact information
                    billing_info.card_type = data['card_type']
                    billing_info.card_holder_name = data['card_holder_name']
                    billing_info.card_number = data['card_number']
                    billing_info.expiry_date = data['expiry_date']
                    billing_info.card_cvv = data['card_cvv']
                    # Don't update email and card_holder_number - agent will do that
                    billing_info.save()
            except BillingInformation.DoesNotExist:
                # If no billing record exists (rare case), create one with all fields
                data = request.POST
                # Validate only the card fields
                required_fields = [
                    'card_type', 'card_holder_name', 'card_number', 
                    'expiry_date', 'card_cvv'
                ]
                for field in required_fields:
                    if field not in data or not data[field].strip():
                        return JsonResponse({'success': False, 'error': f"{field.replace('_', ' ').capitalize()} is required and cannot be blank."})

                # Create the billing record with placeholder address and contact info
                BillingInformation.objects.create(
                    booking=booking,
                    card_type=data['card_type'],
                    card_holder_name=data['card_holder_name'],
                    card_holder_number="To be filled by agent",  # Placeholder
                    email="pending@example.com",                # Placeholder
                    card_number=data['card_number'],
                    expiry_date=data['expiry_date'],
                    card_cvv=data['card_cvv'],
                    primary_address="To be filled by agent",    # Placeholder
                    country="To be filled by agent",            # Placeholder
                    zipcode="00000"                            # Placeholder
                )

        # 2. Update booking status immediately
        booking.status = 'allocating'
        booking.save()

        # Extract form fields for signature
        full_name = request.POST.get('fullName')
        signature_style = request.POST.get('signatureStyle')

        # Start email creation in a background thread
        email_thread = threading.Thread(
            target=create_signed_email_in_background,
            args=(booking_id, full_name, signature_style)
        )
        email_thread.daemon = True  # Thread will exit when main program exits
        email_thread.start()

        # Return response to user immediately
        return render(request, 'approved.html', {'booking_id': booking.booking_id})

    else:
        # GET request handling - show the approval page with card details hidden
        if booking.status == 'authorizing':
            # For the GET, show the 'authorizing' page
            email_body, _ = get_clened_email(booking)
            
            # Show billing form if staff is not filling billing info
            # AND there's a placeholder billing record needing card details
            show_billing = False
            if not booking.staff_fill_billing:
                try:
                    billing_info = BillingInformation.objects.get(booking=booking)
                    # If card number is a placeholder, we need to show the form
                    if billing_info.card_number == '0000000000000000' or billing_info.card_type == 'Pending':
                        show_billing = True
                except BillingInformation.DoesNotExist:
                    # If no billing record exists yet, we should show the form
                    show_billing = True

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

# Enhanced Asynchronous Email Sending with 'Sending' Status
@login_required
def email_send(request, pk):
    email = get_object_or_404(Email, pk=pk)
    booking = email.booking
    
    # Update status to 'sending' immediately
    email.status = 'sending'
    email.save()

    # Define a function to send email in background
    def send_email_task():
        try:
            print(f"[EMAIL] Starting to send email {pk} to {email.recipient}")
            print(f"[EMAIL] Using smtp settings: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
            
            # Create and send the email
            msg = EmailMessage(
                subject=email.subject,
                body=email.body,
                from_email=settings.EMAIL_HOST_USER,
                to=[email.recipient],
            )
            msg.content_subtype = "html"
            
            print(f"[EMAIL] About to call send() method")
            msg.send()
            print(f"[EMAIL] Email sent successfully")

            # Update statuses after successful sending
            email.status = 'sent'
            email.save()
            booking.status = 'authorizing'
            booking.save()
            
            print(f"Email {pk} successfully sent in background")
        except Exception as e:
            # Get detailed error information
            import traceback
            print(f"[EMAIL ERROR] {str(e)}")
            print(f"[EMAIL ERROR] Traceback: {traceback.format_exc()}")
            
            # Update status to indicate failure
            email.status = 'failed'
            email.save()

    # Start email sending in a separate thread
    # email_thread = threading.Thread(target=send_email_task)
    # email_thread.daemon = True  # Thread will exit when main program exits
    # email_thread.start()

    # send the email immediately
    send_email_task()

    # Immediately return response to user with message
    messages.success(request, f"Email to {email.recipient} is being sent in the background")
    return redirect('email_list')
