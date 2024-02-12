from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from .models import Email
import os

def send_email(subject, recipients, message):
    send_mail(
        subject,
        "client doesn't support html emails",
        settings.EMAIL_HOST_USER,
        [recipients],
        fail_silently=False,
        html_message= message,
    )

def save_email(subject, recipient, message, added_by, status= 'sent'):
    email = Email.objects.create(
        subject=subject,
        body=message,
        recipient=recipient,
        status= status,
        added_by= added_by
    )
    email.content_subtype = 'plain'
    email.save()

def create_auth_draft(booking):
    try:
        template = 'email_templates/mybooking_auth.html'
        approval_url = reverse('approve-booking', args=[booking.booking_id])
        passengers = booking.passenger_set.all()
        billing = booking.billinginformation_set.all()
        card_number = billing[0].card_number[-4:]
        card_holder_name = billing[0].card_holder_name
        flights = booking.flightdetails_set.all()
        airline_cost = sum([f.airline_cost for f in flights])
        tax_fee = booking.amount - airline_cost
        adult_count = len(passengers)
        message = render_to_string(template, {'booking': booking, 
                                                'approval_url': os.getenv('HOST_URL') + approval_url, 
                                                'passengers': passengers, 
                                                'tax_fee': tax_fee, 
                                                'airline_cost': airline_cost,
                                                'adult_count': adult_count, 
                                                'flights': flights,
                                                'card_number': card_number,
                                                'card_holder_name': card_holder_name})
    except:
        return None
    return message
