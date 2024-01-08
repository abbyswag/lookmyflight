from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation
from django.core.validators import RegexValidator
from django.forms import ValidationError
import datetime


# Calllog Model
class CallLog(models.Model):
    CATEGORY_CHOICES = (
        ('BID', 'BID'),
        ('Refund', 'Refund'),
        ('FutureCredit', 'Future Credit'),
        ('Other', 'Other'),
    )

    id = models.AutoField(primary_key=True)
    customer_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    call_date = models.DateTimeField(auto_now_add=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default= 'BID')
    remark = models.TextField(blank=True)

    # GenericForeignKey
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default= None, null= True) 


    def save(self, *args, **kwargs):
        # Automatically create a Booking or Refund instance based on the selected category
        if self.category == 'BID':
            related_object = BID.objects.create()
        elif self.category == 'Refund':
            related_object = Refund.objects.create()

        self.content_type = ContentType.objects.get_for_model(related_object)
        self.object_id = related_object.id

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer_name} - {self.phone}"



class CardExpiryValidator(RegexValidator):
    regex = r'^(0[1-9]|1[0-2])(/)(([0-9]){2})$'
    message = 'Expiry date must be in MM/YY format'

    def validate(self, value):
        super().validate(value)
        today = datetime.date.today()
        expiry = datetime.datetime.strptime(value, '%m/%y')
        expiry_date = expiry.replace(year=today.year)
        if expiry_date < today.replace(day=1):
            raise ValidationError('Expiry date cannot be in the past')


class BillingInformation(models.Model):
    card_type_choices = (
        ('Visa', 'Visa'),
        ('MasterCard', 'MasterCard'),
        ('AmericanExpress', 'American Express'),
    )

    card_type = models.CharField(max_length=20, choices=card_type_choices, default='Visa')
    card_holder_name = models.CharField(max_length=255, default=None)
    card_number = models.CharField(
        max_length=16,
        validators=[RegexValidator(r'^\d{16}$', 'Enter a valid 16-digit card number.')], 
        default=None)
    expiry_date = models.CharField(
        max_length=5,
        validators=[CardExpiryValidator()],
        default=None
    )
    card_cvv = models.CharField(
        max_length=4,
        validators=[RegexValidator(r'^\d{3,4}$', 'Enter a valid CVV.')],
        default=None)
    gateway_source = models.CharField(max_length=255, default=None)
    billing_address = models.TextField(default=None)
    bid= models.ForeignKey('BID', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.card_type} - {self.card_holder_name}'
    

# Passenger Model
class Passenger(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    bid= models.ForeignKey('BID', on_delete=models.CASCADE)
    full_passenger_name = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    ticket_number = models.CharField(max_length=50)

def generate_bid_id():
    today = datetime.datetime.now().strftime('%y%m%d')
    existing_bids = BID.objects.filter(bid_id__startswith=f'LMy{today}')
    
    if existing_bids.exists():
        last_bid = existing_bids.order_by('-bid_id').first()
        last_number = int(last_bid.bid_id[-3:])
        new_number = last_number + 1
    else:
        new_number = 1
    
    return f'LMy{today}{str(new_number).zfill(3)}'

# BID model
class BID(models.Model):

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
    )
    PAYMENT_CHOICES = (
        {'waiting', 'Waiting'},
        {'cleared', 'Cleared'},
        {'failed', 'Failed'},
        {'refunded', 'Refunded'},
    )

    # relations
    call_logs = GenericRelation(CallLog, related_query_name='bid_call_logs')
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default= None, null= True)

    # flight information
    airline_name = models.CharField(max_length=255, blank=True, null=True)
    airline_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default= 'USD')
    gds_pnr = models.CharField(max_length=50, default=None, blank= True, null=True)
    from_location = models.CharField(max_length=255, blank= True, null=True)
    to_location = models.CharField(max_length=255, blank= True, null=True)  
    departure_datetime = models.DateTimeField(blank= True, null=True)
    arrival_datetime = models.DateTimeField(blank= True, null=True)
    flight_number = models.CharField(max_length=10, blank= True, null=True)

    @property
    def duration(self):
        return self.arrival_datetime - self.departure_datetime
    
    # booking information
    bid_id = models.CharField(max_length=8, unique=True, default=generate_bid_id)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initiated')
    mco = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='initiated')
    agent_remarks = models.TextField(default=str, blank= True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        customer_name = self.call_logs.first().customer_name if self.call_logs.exists() else "N/A"
        return f'BID ID: {self.bid_id} - Customer Name: {customer_name}'

# Refund Model
class Refund(models.Model):
    CURRENCY_CHOICES = (
        ('USD', 'USD'),
        ('GBP', 'GBP'),
        ('CAD', 'CAD'),
    )
    STATUS_CHOICES = (
        ('requested', 'Requested'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    )

    call_logs = GenericRelation(CallLog, related_query_name='refund_call_logs')

    # refund information
    refund_id = models.CharField(max_length=8, unique=True, default=generate_bid_id)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, default= '0', blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    reason = models.TextField(default="", blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'Refund ID: {self.refund_id} - Amount: {self.amount} {self.currency}'

# FutureCredit Model
class FutureCredit(models.Model):
    CURRENCY_CHOICES = (
        ('USD', 'USD'),
        ('GBP', 'GBP'),
        ('CAD', 'CAD'),
    )
    STATUS_CHOICES = (
        ('requested', 'Requested'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    )

    call_logs = GenericRelation(CallLog, related_query_name='future_credit_call_logs')

    # future credit information
    future_credit_id = models.CharField(max_length=8, unique=True, default=generate_bid_id)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    reason = models.TextField(default="", blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'Future Credit ID: {self.future_credit_id} - Amount: {self.amount} {self.currency}'


# Email Model
class Email(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('sent', 'Sent'),
    )

    subject = models.CharField(max_length=255)
    body = models.TextField()
    recipient = models.EmailField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
