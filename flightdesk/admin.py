from django.contrib import admin
from django import forms
from django.forms import inlineformset_factory
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.utils.html import format_html
from django.db import models
from django.urls import reverse
from django.forms import ClearableFileInput
from django.shortcuts import get_object_or_404
from django.contrib.admin.widgets import AdminFileWidget
from django.conf import settings
import clipboard
from django.utils.safestring import mark_safe

from django.urls import path

from .models import Passenger, BillingInformation, CallLog, Booking, Email, Refund, FutureCredit

class CallLogAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'call_date', 'category')
    exclude = ('added_by',)

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

class CustomAdminFileWidget(AdminFileWidget):
    def render(self, name, value, attrs=None, renderer=None):
        result = []
        if hasattr(value, "url"):
            result.append(
                f'''<a href="{value.url}" target="_blank">
                      <img 
                        src="{value.url}" alt="{value}" 
                        width="100" height="100"
                        style="object-fit: cover;"
                      />
                    </a>'''
            )
        result.append(super().render(name, value, attrs, renderer))
        return format_html("".join(result))

class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_id', 'customer_name', 'amount', 'status', 'payment_status')
    exclude = ('added_by',)
    actions = ['send_email', 'edit_email']
    inlines = [BillingInformationInline, PassengerInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('currency', 'amount','status', 'payment_status', 'agent_remarks')
        }),
        # ('Billing Information', {
        #     'fields': ('card_type', 'card_holder_name', 'card_number', 'expiry_date', 'card_cvv', 'gateway_source', 'billing_address')
        # }),
        ('Flight Information', {
            'fields': ('airline_name','airline_cost','gds_pnr', 'confirmation_arl', 'ticket_image')
        }),
        # ('MCO Information', {
        #     'fields': ('mco_description','mco_number')
        # }),
    )

    list_filter = (BookingStatusFilter, 'created_at')
    # list_filter = ('status', '')

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
    
    # def customer_name(self, obj):
    #     return obj.call_logs.first().customer_name if obj.call_logs.exists() else "N/A"
    def save_model(self, request, obj, form, change):
        obj.added_by = request.user
        old_obj = self.model.objects.get(pk=obj.pk) if change else None  
        
        # Save the model
        super().save_model(request, obj, form, change)

        # Check if the status has changed
        if change and obj.status != old_obj.status:
            self.create_email_draft(obj)


    def create_email_draft(self, booking):
        subject = f"Booking Status Changed: {booking.booking_id}"
        approval_url = 'https://chat.openai.com/c/1a28a960-3619-471f-9396-9d816dfa30b9'
        message = render_to_string('email_templates/booking_status_change.html', {'booking': booking, 'approval_url': approval_url})
        message = strip_tags(message)
        
        email = Email.objects.create(
            subject=subject,
            body=message,
            recipient=booking.call_logs.first().email,
            status='draft',
        )
        email.content_subtype = 'plain' 
        email.save()


class EmailAdmin(admin.ModelAdmin):
    list_display = ('subject', 'recipient', 'status', 'send_email_button')

    actions = ['send_selected_emails']

    def send_email_button(self, obj):
        if obj.status == 'draft':
            # return format_html('<a class="button" href="{}">Send Email</a>', reverse('admin:send_email', args=[obj.id]))
            pass
        else:
            return 'N/A'

    send_email_button.short_description = 'Send Email'

    def send_selected_emails(modeladmin, request, queryset):
        for email in queryset:
            if email.status == 'draft':
                send_mail(
                    email.subject,
                    'demo',
                    settings.EMAIL_HOST_USER,
                    [email.recipient],
                    fail_silently=False,
                    html_message= email.body,
                )
                email.status = 'sent'
                email.save()

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
admin.site.register(Booking, BookingAdmin)
admin.site.register(Refund, RefundAdmin)
