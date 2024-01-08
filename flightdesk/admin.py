from django.contrib import admin
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.utils.html import format_html
from django.contrib.admin.widgets import AdminFileWidget
from django.conf import settings
from django.urls import reverse
from datetime import datetime, timedelta

from .models import Passenger, BillingInformation, CallLog, BID, Email, Refund, FutureCredit

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
    list_display = ('bid_id', 'customer_name', 'amount', 'status', 'mco')
    exclude = ('added_by',)
    actions = ['send_email']
    inlines = [BillingInformationInline, PassengerInline]
    list_filter = (BookingStatusFilter, 'created_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('currency', 'amount','status', 'mco', 'agent_remarks')
        }),
        ('Flight Information', {
            'fields': ('airline_name','airline_cost', 'flight_number', 'from_location', 'to_location', 'departure_datetime', 'arrival_datetime','gds_pnr')
        }),
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

    def create_auth_draft(self, booking):
        subject = f"Booking Authorization Started: {booking.bid_id}" 
        template = 'email_templates/bid_auth.html'
        approval_url = reverse('approve-booking', args=[booking.bid_id])
        passengers = booking.passenger_set.all()
        tax_fee = booking.amount - booking.airline_cost
        adult_count = len(passengers)
        message = render_to_string(template, {'booking': booking, 'approval_url': approval_url, 'passengers': passengers, 'tax_fee': tax_fee, 'adult_count': adult_count})
        email = Email.objects.create(
            subject=subject,
            body=message,
            recipient=booking.call_logs.first().email,
            status='draft',
        )
        email.content_subtype = 'plain' 
        email.save()

    def create_conf_draft(self, booking):
        subject = f"Booking Confirmed: {booking.booking_id}"
        message = render_to_string('email_templates/bid_conf.html', {'booking': booking})
        email = Email.objects.create(
            subject=subject,
            body=message,
            recipient=booking.call_logs.first().email,
            status='draft',
        )
        email.content_subtype = 'plain' 
        email.save()


class EmailAdmin(admin.ModelAdmin):
    list_display = ('subject', 'recipient', 'status')
    actions = ['send_selected_emails']
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
admin.site.register(BID, BookingAdmin)
admin.site.register(Refund, RefundAdmin)
