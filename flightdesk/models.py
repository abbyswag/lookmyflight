from django.db import models
from django.urls import reverse
from django.conf import settings
from django.dispatch import receiver
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.core.validators import RegexValidator
from django.template.loader import render_to_string
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

file_path = os.path.join(settings.BASE_DIR,'flightdesk/airport_data')
with open(file_path, 'rb') as file:
    airport_dict = pickle.load(file)

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

    # def save(self, *args, **kwargs):
    #     if self.category == 'New Booking':
    #         related_object = NewBooking.objects.create(added_by=self.added_by)
    #     elif self.category == 'Cancelation':
    #         related_object = Cancellation.objects.create(added_by=self.added_by)
    #     elif self.category == 'Addition':
    #         related_object = Addition.objects.create(added_by=self.added_by)
    #     else:
    #         related_object = None

    #     try:
    #         self.content_type = ContentType.objects.get_for_model(related_object)
    #         self.object_id = related_object.id
    #     except: pass
    #     super().save(*args, **kwargs)

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
    card_number = models.CharField(
        max_length=16,
        validators=[RegexValidator(r'^\d{16}$', 'Enter a valid 16-digit card number.')])
    expiry_date = models.CharField(
        max_length=5,
        validators=[CardExpiryValidator()])
    card_cvv = models.CharField(
        max_length=4,
        validators=[RegexValidator(r'^\d{3,4}$', 'Enter a valid CVV.')])
    gateway_source = models.CharField(max_length=50, default = 'LOOKMYFLIGHT')
    billing_address = models.TextField()

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


class FlightDetails(models.Model):

    CURRENCY_CHOICES = (
        ('USD', 'USD'),
        ('GBP', 'GBP'),
        ('CAD', 'CAD'),
    )
        
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE)
    airline_name = models.CharField(max_length=255)
    airline_cost = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default= 'USD')
    gds_pnr = models.CharField(max_length=50, default=None)
    from_location = models.CharField(max_length=255)
    to_location = models.CharField(max_length=255)  
    departure_datetime = models.DateTimeField()
    arrival_datetime = models.DateTimeField()
    flight_number = models.CharField(max_length=10)

    @property
    def duration(self):
        return self.arrival_datetime - self.departure_datetime
    
    def set_airport_names_from_iata_code(self):
        self.from_location = airport_dict.get(self.from_location.upper())
        self.to_location = airport_dict.get(self.to_location.upper())

    def save(self, *args, **kwargs):
        self.set_airport_names_from_iata_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'FlightDetails for Booking ID: {self.booking.booking_id}'

# Booking model
class Booking(models.Model):

    CURRENCY_CHOICES = (
        ('USD', 'USD'),
        ('GBP', 'GBP'),
        ('CAD', 'CAD'),
    )
    STATUS_CHOICES = (
        ('initiated', 'Initiated'),
        ('authorizing', 'Authorizing'),
        ('allocating', 'Allocating'),
        ('confirmed', 'Confirmed'), 
        ('cleared', 'Cleared'), 
    )

    # relations
    call_logs = GenericRelation(CallLog, related_query_name='mybooking_call_logs')
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default= None, null= True)
    
    # booking information
    booking_id = models.CharField(max_length=8, unique=True, default=generate_mybooking_id)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default= 'USD')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default = 0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initiated')
    agent_remarks = models.TextField(default=str, blank= True)
    created_at = models.DateTimeField(auto_now_add=True)


class NewBooking(Booking):
    e_ticket = models.ImageField(upload_to='e_tickets', blank=True)
    boarding_pass = models.ImageField(upload_to='boarding_passes', blank=True)

    def __str__(self):
        customer_name = self.call_logs.first().customer_name if self.call_logs.exists() else "N/A"
        return f'New Booking of {self.booking_id} - Customer Name: {customer_name}'

class Cancellation(Booking):
    REASON_CHOICES = (
        ('Schedule change', 'Schedule change'),
        ('Personal reason', 'Personal reason'),
        ('Price too high', 'Price too high'),
        ('Other', 'Other'),
    )

    reason = models.CharField(max_length=100, choices=REASON_CHOICES)
    pnr = models.CharField(max_length=20, unique=True)

    def __str__(self):
        customer_name = self.call_logs.first().customer_name if self.call_logs.exists() else "N/A"
        return f'Cancellation of {self.booking_id} - {customer_name}'

class AddInline(models.Model):

    weight = models.DecimalField(decimal_places = 2, max_digits = 5, default = 0)
    pet_type = models.CharField(max_length = 10, default = 'None')
    no_of_meals = models.CharField(max_length = 1, default = 0)

class Addition(Booking):
    CHOICES = (
        ('Baggage', 'Baggage'),
        ('Meal', 'Meal'),
        ('Pet', 'Pet'),
    )
    
    category = models.CharField(max_length=100, choices=CHOICES)
    pnr = models.CharField(max_length=20, unique=True)

    def __str__(self):
        customer_name = self.call_logs.first().customer_name if self.call_logs.exists() else "N/A"
        return f'Addition of {self.booking_id} - {customer_name}'

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

