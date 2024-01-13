from django.contrib import admin
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.utils.html import format_html
from django.conf import settings
from django.urls import reverse
import os
from .models import Passenger, BillingInformation, CallLog, MyBooking, Email, Refund, FutureCredit, FlightDetails, EmailAttachtment


class CallLogAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'call_date', 'category')
    exclude = ('added_by', 'object_id', 'content_type')

    def save_model(self, request, obj, form, change):
        obj.added_by = request.user
        super().save_model(request, obj, form, change)

    def get_list_filter(self, request):
        if request.user.groups.filter(name='supervisor').exists():
            self.list_filter = ('added_by',)
        return super().get_list_filter(request)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        
        if request.user.groups.filter(name='agent').exists():
            return qs.filter(added_by=request.user)
        return qs


class BookingStatusFilter(admin.SimpleListFilter):
    title = 'Booking Status'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            ('initiated', 'Initiated'),
            ('authorizing', 'Authorizing'),
            ('allocating', 'Allocating'),
            ('confirmed', 'Confirmed'),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())


class PassengerInline(admin.TabularInline):
    model = Passenger
    extra = 1


class BillingInformationInline(admin.StackedInline):
    model = BillingInformation
    can_delete = False
    verbose_name_plural = 'Billing Details'
    extra = 1


class FlightDetailsInline(admin.StackedInline):
    model = FlightDetails
    can_delete = False
    verbose_name_plural = "Flight Details"
    extra = 1


class BookingAdmin(admin.ModelAdmin):
    list_display = ('mybooking_id', 'customer_name', 'amount', 'status', 'mco')
    exclude = ('added_by',)
    actions = ['send_email']
    inlines = [BillingInformationInline, PassengerInline, FlightDetailsInline]
    list_filter = (BookingStatusFilter, 'created_at')
    fieldsets = (
        ('General', {
            'fields': ('currency', 'amount','status', 'mco', 'agent_remarks')
        }),
        ('ticket/pass', {
            'fields': ('e_ticket', 'boarding_pass')
        })
    )

    def save_model(self, request, obj, form, change):
        obj.added_by = request.user
        super().save_model(request, obj, form, change)

    def get_list_filter(self, request):
        if request.user.groups.filter(name='supervisor').exists():
            self.list_filter = ('added_by',)
        return super().get_list_filter(request)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        
        if request.user.groups.filter(name='agent').exists():
            return qs.filter(added_by=request.user)
        return qs
    
    def customer_name(self, obj):
        return obj.call_logs.filter(id__isnull=False).first().customer_name if obj.call_logs.exists() else "N/A"

    def save_model(self, request, obj, form, change):
        obj.added_by = request.user
        old_obj = self.model.objects.get(pk=obj.pk) if change else None  

        super().save_model(request, obj, form, change)
        if change and obj.status == 'authorizing' and old_obj.status == 'initiated':
            self.create_auth_draft(obj)
        elif change and obj.status == 'confirmed' and old_obj.status == 'allocating':
            self.create_conf_draft(obj)
        elif change and obj.status == 'cleared' and old_obj.status == 'confirmed':
            self.create_clrd_draft(obj)

    def create_auth_draft(self, booking):
        subject = f"Booking Authorization Started: {booking.mybooking_id}" 
        template = 'email_templates/mybooking_auth.html'
        approval_url = reverse('approve-booking', args=[booking.mybooking_id])
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
        email = Email.objects.create(
            subject=subject,
            body=message,
            recipient=booking.call_logs.first().email,
            status='draft',
            added_by=booking.added_by
        )
        email.content_subtype = 'plain' 
        email.save()

    def create_conf_draft(self, booking):
        subject = f"Booking Confirmed: {booking.mybooking_id}"
        if booking.e_ticket:
            ticket_url = booking.e_ticket.url
        message = render_to_string('email_templates/mybooking_conf.html', {'ticket_url': os.getenv('HOST_URL') + ticket_url})
        email = Email.objects.create(
            subject=subject,
            body=message,
            recipient=booking.call_logs.first().email,
            status='draft',
        )
        email.content_subtype = 'plain' 
        email.save()

    def create_clrd_draft(self, booking):
        subject = f"Booking Cleared: {booking.mybooking_id}"
        if booking.boarding_pass:
            pass_url = booking.boarding_pass.url
        pass
        message = render_to_string('email_templates/mybooking_clrd.html', {'pass_url': os.getenv('HOST_URL') + pass_url})
        email = Email.objects.create(
            subject=subject,
            body=message,
            recipient=booking.call_logs.first().email,
            status='draft',
        )
        email.content_subtype = 'plain' 
        email.save()

class EmailAttachtmentInline(admin.StackedInline):
    model = EmailAttachtment
    can_delete = False
    verbose_name_plural = "Attachment"
    extra = 1    


class EmailAdmin(admin.ModelAdmin):
    list_display = ('subject', 'recipient', 'status')
    inlines = [EmailAttachtmentInline]
    actions = ['send_selected_emails']
    readonly_fields = ('preview', )
    fieldsets = (
        ('Preview', {
            'fields': ('preview',)
        }),        
        ('General', {
            'fields': ('subject', 'recipient', 'body', 'status')
        }),
    )

    def preview(self, instance):
        html_content = instance.body
        return format_html(html_content)
    
    def get_list_filter(self, request):
        if request.user.groups.filter(name='supervisor').exists():
            self.list_filter = ('added_by',)
        return super().get_list_filter(request)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        
        if request.user.groups.filter(name='agent').exists():
            return qs.filter(added_by=request.user)
        return qs
    
    def send_selected_emails(modeladmin, request, queryset):
        for email in queryset:
            if email.status == 'draft':
                send_mail(
                    email.subject,
                    "client doesn't support html emails",
                    settings.EMAIL_HOST_USER,
                    [email.recipient],
                    fail_silently=False,
                    html_message= email.body,
                )
                email.status = 'sent'
                email.save()

    preview.short_description = ''
    send_selected_emails.short_description = 'Send selected emails'


class RefundAdmin(admin.ModelAdmin):
    list_display = ('refund_id', 'currency', 'amount', 'status', 'reason', 'processed_at')
    search_fields = ('refund_id', 'reason')
    list_filter = ('status', 'processed_at')
    date_hierarchy = 'processed_at'
    readonly_fields = ('processed_at',)  


class FutureCreditAdmin(admin.ModelAdmin):
    list_display = ('future_credit_id', 'currency', 'amount', 'status', 'reason', 'processed_at')
    search_fields = ('future_credit_id', 'reason')
    list_filter = ('status', 'processed_at')
    date_hierarchy = 'processed_at'
    readonly_fields = ('processed_at',)


admin.site.register(FutureCredit, FutureCreditAdmin)
admin.site.register(Email, EmailAdmin)
admin.site.register(CallLog, CallLogAdmin)
admin.site.register(MyBooking, BookingAdmin)
admin.site.register(Refund, RefundAdmin)
