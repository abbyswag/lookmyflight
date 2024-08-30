from django.db import models
from django.urls import reverse
from django.conf import settings
from django.dispatch import receiver
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.core.validators import RegexValidator
from django.template.loader import render_to_string
from django.core.validators import RegexValidator, EmailValidator
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation

import datetime, os, pickle
from .validators import CardExpiryValidator

# utils functions/scripts
def generate_mybooking_id():
    today = datetime.datetime.now().strftime('%y%m%d')
    existing_mybookings = Booking.objects.filter(booking_id__startswith=f'LM{today}')
    
    if existing_mybookings.exists():
        last_mybooking = existing_mybookings.order_by('-booking_id').first()
        last_number = int(last_mybooking.booking_id[-3:])
        new_number = last_number + 1
    else:
        new_number = 1
    
    return f'LM{today}{str(new_number).zfill(3)}'

# Campaign Model
class Campaign(models.Model):
    code = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.code


# Calllog Model
class CallLog(models.Model):
    TAG_CHOICES = (
        ('LMF', 'LMF'),
        ('877', '877'),
        ('TOH', 'TOH'),
        ('Other', 'Other'),
    )

    CONVERT_CHOICES = (
        ('Yes', 'Yes'),
        ('No', 'No'),
    )

    id = models.AutoField(primary_key=True)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default= None, null= True) 
    converted = models.CharField(max_length=5, choices=CONVERT_CHOICES, default='Yes')
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    call_date = models.DateTimeField(auto_now_add=True)
    tag = models.ForeignKey(Campaign, on_delete=models.SET_NULL, null=True, blank=True)
    concern = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} - {self.phone}"


# BillingInformation Model
class BillingInformation(models.Model):

    card_type_choices = (
        ('Visa', 'Visa'),
        ('MasterCard', 'MasterCard'),
        ('AmericanExpress', 'American Express'),
    )
    booking= models.ForeignKey('Booking', on_delete=models.CASCADE)
    card_type = models.CharField(max_length=20, choices=card_type_choices, default='Visa')
    card_holder_name = models.CharField(max_length=255)
    card_holder_number = models.CharField(max_length=20)
    email = models.EmailField(max_length=254, validators=[EmailValidator()])
    
    card_number = models.CharField(
        max_length=16,
        validators=[RegexValidator(r'^\d{16}$', 'Enter a valid 16-digit card number.')])
    expiry_date = models.CharField(
        max_length=5,
        validators=[CardExpiryValidator()])
    card_cvv = models.CharField(
        max_length=4,
        validators=[RegexValidator(r'^\d{3,4}$', 'Enter a valid CVV.')])
    
    primary_address = models.TextField()
    country = models.CharField(max_length=100)
    zipcode = models.CharField(
        max_length=10,
        validators=[RegexValidator(r'^\d{5}(-\d{4})?$', 'Enter a valid ZIP code.')])

    def __str__(self):
        return f'{self.card_type} - {self.card_holder_name}'
    

# Passenger Model
class Passenger(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    booking= models.ForeignKey('Booking', on_delete=models.CASCADE)
    full_passenger_name = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    ticket_number = models.CharField(max_length=50, blank=True)


# Booking Model
class Booking(models.Model):
    CURRENCY_CHOICES = (
        ('CAD', 'CAD'),
        ('USD', 'USD'),
        ('GBP', 'GBP'),
    )

    STATUS_CHOICES = (
        ('initiated', 'Initiated'),
        ('authorizing', 'Authorizing'),
        ('allocating', 'Allocating'),
        ('confirmed', 'Confirmed'), 
        ('cleared', 'Cleared'), 
    )

    booking_id = models.CharField(max_length=20, unique=True, default=generate_mybooking_id, editable=False)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES)
    mco = models.IntegerField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='initiated')
    created_at = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    regarding_flight = models.BooleanField(default=False)
    regarding_hotel = models.BooleanField(default=False)
    regarding_vehicle = models.BooleanField(default=False)
    subcategory = models.CharField(max_length=255, blank=True)

    call_log = models.ForeignKey(CallLog, on_delete=models.SET_NULL, null=True, blank=True)
    
    flight_info_img = models.ImageField(upload_to='booking/flight_info/', null=True, blank=True)
    hotel_info_img = models.ImageField(upload_to='booking/hotel_info/', null=True, blank=True)
    vehicle_info_img = models.ImageField(upload_to='booking/vehicle_info/', null=True, blank=True)

    def __str__(self):
        return f"Booking {self.booking_id} - {self.status}"


@receiver(post_save, sender=Booking)
def create_notification(sender, instance, created, **kwargs):
    if not created and instance.status == 'allocating':
        template = 'email_templates/mybooking_notification.html'
        url = reverse('admin:flightdesk_newbooking_change', args=[instance.pk])
        supervisors = User.objects.filter(groups__name='supervisor')
        recipients = [user.email for user in supervisors]
        message = render_to_string(template, {'booking_id': instance.booking_id, 'url': os.getenv('HOST_URL') + url})
        send_mail(
            'Payment for boooking {}'.format(instance.booking_id),
            "client doesn't support html emails",
            settings.EMAIL_HOST_USER,
            ['charges@lookmyflight.com'],  
            fail_silently=False,
            html_message= message,
        )
        

class EmailAttachtment(models.Model):
    email= models.ForeignKey('Email', on_delete=models.CASCADE)
    attachment = models.ImageField(upload_to='email_attachments', blank= True)

# Email Model
class Email(models.Model):

    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('sent', 'Sent'),
    )

    subject = models.CharField(max_length=255)
    recipient = models.EmailField()
    body = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default= None, null= True, related_name = 'creator') 

