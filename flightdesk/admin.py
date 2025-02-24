from django.contrib import admin
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.utils.html import format_html
from django.conf import settings
from django.urls import reverse
from django.db.models import Q
import os
from .utils import send_email, save_email, create_auth_draft
from .models import Passenger, BillingInformation, CallLog, Email, EmailAttachtment, Campaign, PrivateChat, PrivateMessage

class CustomerNameRegexFilter(admin.SimpleListFilter):
  title = 'name'
  parameter_name = 'name'

  def lookups(self, request, model_admin):    
    customer_names = CallLog.objects.values_list('name', flat=True).distinct()
    customer_lookups = [(name, name) for name in customer_names]

    return customer_lookups

  def queryset(self, request, queryset):
    if self.value():
        regex = r'(?i).*%s$' % self.pattern
        return queryset.filter(Q(name__iregex=regex))
      
    return queryset

  @property
  def pattern(self):
    return self.used_parameters.get('name')

class CallLogAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'tag', 'converted',)
    exclude = ('added_by',)
    fieldsets = (
        ('Customer', {
            'fields': ('name', 'phone', 'email', 'tag', 'converted', 'concern')
        }),
    )
    # list_filter = ('call_date', 'tag', 'converted', CustomerNameRegexFilter, )

    def save_model(self, request, obj, form, change):
        obj.added_by = request.user
        super().save_model(request, obj, form, change)

    def get_list_filter(self, request):
        if request.user.groups.filter(name='supervisor').exists():
            self.list_filter = ('added_by','call_date', 'tag', CustomerNameRegexFilter, )
        else:
            self.list_filter = ('call_date', 'tag', CustomerNameRegexFilter, )
        return super().get_list_filter(request)

    # def get_queryset(self, request):
    #     qs = super().get_queryset(request)
    #     if request.user.groups.filter(name='agent').exists():
    #         return qs.filter(added_by=request.user)
    #     return qs


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



class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_id', 'customer_name', 'amount', 'status')
    exclude = ('added_by', )
    inlines = [ PassengerInline]
    list_filter = (BookingStatusFilter, 'created_at',)
    fieldsets = (
        ('General', {
            'fields': ('currency', 'amount', 'agent_remarks')
        }),
        ('ticket/pass', {
            'fields': ('e_ticket', 'boarding_pass')
        })
    )

    def get_list_filter(self, request):
        if request.user.groups.filter(name='supervisor').exists():
            self.list_filter = (BookingStatusFilter, 'created_at', 'added_by',)
        return super().get_list_filter(request)

    # def get_queryset(self, request):
    #     qs = super().get_queryset(request)
    #     if request.user.groups.filter(name='agent').exists():
    #         return qs.filter(added_by=request.user)
    #     return qs
    
    def customer_name(self, obj):
        return obj.call_logs.filter(id__isnull=False).first().customer_name if obj.call_logs.exists() else "N/A"

    def save_model(self, request, obj, form, change):
        obj.added_by = request.user
        super().save_model(request, obj, form, change)


class NewBookingAdmin(BookingAdmin):
    fieldsets = (
        ('General', {
            'fields': ('currency', 'status', 'amount', 'agent_remarks')
        }),
        ('ticket/pass', {
            'fields': ('e_ticket', 'boarding_pass')
        })
    )
    actions = ['draft_approval_email' ,'send_approval_email', 'send_ticket', 'send_boarding_pass']

    def draft_approval_email(self, request, queryset):
        self.send_approval_email(request, queryset, False)
        # self.message_user(request, f'{queryset.count()} booking(s) authorization mail draft created.')
    draft_approval_email.short_description = 'draft approval email'

    def send_approval_email(self, request, queryset, status= True):
        flag = False
        for booking in queryset:
            if booking.status == 'authorizing':
                flag = True
                self.message_user(request, f'{queryset.count()} booking(s) approval email already sended (No need to send multiple time).')
            else:
                subject = f"Booking Authorization Started: {booking.booking_id}" 
                recipient = booking.call_logs.first().email
                message = create_auth_draft(booking)
                print(message)
                if message is not None:
                    print(booking)
                    if status: 
                        send_email(subject, recipient, message)
                        save_email(subject, recipient, message, booking.added_by)
                    else: 
                        save_email(subject, recipient, message, booking.added_by, 'draft')
                    booking.status = 'authorizing'
                    booking.save()
                else:
                    flag = True
                    self.message_user(request, f'{queryset.count()} booking(s) approval email not sended (Please fill the details first).')
        if not flag:
            self.message_user(request, f'{queryset.count()} booking(s) authorization mail sended successfully.')
    send_approval_email.short_description = "send approval email"
    
    def send_ticket(self, request, queryset):
        flag = False
        for booking in queryset:
            if booking.status == 'allocating':
                subject = f"Booking Confirmed: {booking.booking_id}"
                recipient=booking.call_logs.first().email
                if booking.e_ticket: ticket_url = booking.e_ticket.url
                else: 
                    flag = True
                    self.message_user(request, 'Please upload the e-ticket first')
                    break
                message = render_to_string('email_templates/mybooking_conf.html', {'ticket_url': os.getenv('HOST_URL') + ticket_url})
                send_email(subject, recipient, message)
                save_email(subject, recipient, message, booking.added_by)
                booking.status = 'confirmed'
                booking.save()
            else: 
                flag = True
                self.message_user(request, 'You can send ticket email after allocation')
                break
        if not flag:
            self.message_user(request, f'{queryset.count()} booking(s) ticket email sended successfully.')
    send_ticket.short_description = 'sent ticket email'

    def send_boarding_pass(self, request, queryset):
        flag = False
        for booking in queryset:
            if booking.status == 'confirmed':
                subject = f"Booking Cleared: {booking.booking_id}"
                recipient=booking.call_logs.first().email
                if booking.boarding_pass: pass_url = booking.boarding_pass.url
                else: 
                    flag = True
                    self.message_user(request, 'Please upload the boarding pass first')
                    break
                message = render_to_string('email_templates/mybooking_clrd.html', {'pass_url': os.getenv('HOST_URL') + pass_url})
                send_email(subject, recipient, message)
                save_email(subject, recipient, message, booking.added_by)
                booking.status = 'confirmed'
                booking.save()
            else: 
                flag = True
                self.message_user(request, 'You can send boarding pass email after confirmation')
                break
        if not flag:
            self.message_user(request, f'{queryset.count()} booking(s) boarding pass email sended successfully.')
    send_boarding_pass.short_description = 'sent boarding pass email'
    
class CancellationAdmin(BookingAdmin):
    fieldsets = (
        ('General', {
            'fields': ('currency', 'amount', 'reason', 'agent_remarks')
        }),
    )


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

    # def get_queryset(self, request):
    #     qs = super().get_queryset(request)
        
    #     if request.user.groups.filter(name='agent').exists():
    #         return qs.filter(added_by=request.user)
    #     return qs
    
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

class CampaignAdmin(admin.ModelAdmin):
    list_display = ('code',)

admin.site.register(Campaign, CampaignAdmin)
admin.site.register(Email, EmailAdmin)
admin.site.register(CallLog, CallLogAdmin)


@admin.register(PrivateChat)
class PrivateChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'user1', 'user2', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user1__username', 'user2__username')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)


@admin.register(PrivateMessage)
class PrivateMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat', 'sender', 'content_snippet', 'timestamp', 'read')
    list_filter = ('read', 'timestamp')
    search_fields = ('sender__username', 'chat__user1__username', 'chat__user2__username', 'content')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)

    def content_snippet(self, obj):
        # Show the first 50 characters of the content
        return obj.content[:50] + ("..." if len(obj.content) > 50 else "")
    content_snippet.short_description = 'Message Content'