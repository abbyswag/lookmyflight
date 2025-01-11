import openpyxl
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
from flightdesk.views import *


@login_required
@user_passes_test(is_supervisor)
def download_call_log_excel(request):
    # Get filter parameters
    filter_value = request.GET.get('filter', 'today')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Initialize a queryset
    call_logs = CallLog.objects.all()

    # Apply filtering based on the filter_value
    if filter_value == 'today':
        # Filter for today
        start_of_day = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = timezone.now().replace(hour=23, minute=59, second=59, microsecond=999999)
        call_logs = call_logs.filter(call_date__range=(start_of_day, end_of_day))
    elif filter_value == 'last_week':
        # Filter for the last 7 days
        last_week = timezone.now() - timedelta(days=7)
        call_logs = call_logs.filter(call_date__gte=last_week)
    elif filter_value == 'last_month':
        # Filter for the last 30 days
        last_month = timezone.now() - timedelta(days=30)
        call_logs = call_logs.filter(call_date__gte=last_month)
    elif start_date and end_date:
        # Filter by custom date range
        call_logs = call_logs.filter(call_date__range=(start_date, end_date))

    # Create an Excel workbook and active sheet
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = 'Call Logs Report'

    # Define the header row
    headers = [
        'ID', 'Name', 'Phone', 'Email', 'Call Date', 'Tag', 'Query Type', 'Airline', 'Concern', 'Converted', 'Added By'
    ]
    sheet.append(headers)

    # Populate the Excel rows
    for log in call_logs:
        sheet.append([
            log.id,
            log.name,
            log.phone,
            log.email if log.email else "null",
            log.call_date.strftime('%Y-%m-%d %H:%M:%S'),
            log.tag.code if log.tag else "null",
            log.query_type.code if log.query_type else "null",
            log.airline.code if log.airline else "null",
            log.concern if log.concern else "null",
            log.converted if log.converted else "null",
            log.added_by.username if log.added_by else "null"
        ])

    # Set the content type and headers for the Excel file download
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=call_logs_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

    # Save the Excel file to the response
    workbook.save(response)
    return response

@login_required
@user_passes_test(is_supervisor)
def download_bookings_excel(request):
    # Get filter parameters
    filter_value = request.GET.get('filter', 'today')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Initialize a queryset
    bookings = Booking.objects.all()

    # Apply filtering based on the filter_value
    if filter_value == 'today':
        # Filter for today
        start_of_day = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = timezone.now().replace(hour=23, minute=59, second=59, microsecond=999999)
        bookings = bookings.filter(created_at__range=(start_of_day, end_of_day))
    elif filter_value == 'last_week':
        # Filter for the last 7 days
        last_week = timezone.now() - timedelta(days=7)
        bookings = bookings.filter(created_at__gte=last_week)
    elif filter_value == 'last_month':
        # Filter for the last 30 days
        last_month = timezone.now() - timedelta(days=30)
        bookings = bookings.filter(created_at__gte=last_month)
    elif start_date and end_date:
        # Filter by custom date range
        bookings = bookings.filter(created_at__range=(start_date, end_date))

    # Create an Excel workbook and active sheet
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = 'Bookings Report'

    # Define the header row
    headers = [
        'Booking ID', 'Currency', 'MCO', 'Status', 'Created At', 'Added By', 
        'Regarding Flight', 'Regarding Hotel', 'Regarding Vehicle', 
        'Flight Cost', 'Hotel Cost', 'Vehicle Cost'
    ]
    sheet.append(headers)

    # Populate the Excel rows
    for booking in bookings:
        sheet.append([
            booking.booking_id,
            booking.currency,
            booking.mco,
            booking.status,
            booking.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            booking.added_by.username if booking.added_by else "null",
            booking.regarding_flight,
            booking.regarding_hotel,
            booking.regarding_vehicle,
            booking.flight_cost,
            booking.hotel_cost,
            booking.vehicle_cost
        ])

    # Set the content type and headers for the Excel file download
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=bookings_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

    # Save the Excel file to the response
    workbook.save(response)
    return response

@login_required
def dashboard(request):
    user = request.user
    if is_agent(user):
        return redirect('agent_dashboard')

    is_supervisor = user.groups.filter(name='supervisor').exists()

    tags = Campaign.objects.all()
    query_types = Query.objects.all()

    context = {
        'is_supervisor': is_supervisor,
        'tags': tags,
        'query_types': query_types,
    }

    return render(request, 'crm/dashboard.html', context)


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from datetime import datetime, timedelta

@login_required
def agent_dashboard(request):
    user = request.user

    # Fetch the current month
    today = datetime.now()
    start_of_month = today.replace(day=1)
    end_of_month = today.replace(day=1) + timedelta(days=32)
    end_of_month = end_of_month.replace(day=1) - timedelta(days=1)

    # Filter bookings and call logs for the current month by the logged-in user
    bookings = Booking.objects.filter(
        added_by=user,
        created_at__date__gte=start_of_month,
        created_at__date__lte=end_of_month
    )
    call_logs = CallLog.objects.filter(
        added_by=user,
        call_date__date__gte=start_of_month,
        call_date__date__lte=end_of_month
    )

    # Prepare days in the current month
    days_in_month = list(range(1, end_of_month.day + 1))

    # Booking stats
    statuses = dict(Booking.STATUS_CHOICES)
    status_counts = [
        {
            'status_code': status,
            'status_label': statuses[status],
            'counts': [0] * end_of_month.day  # Initialize counts for each day
        }
        for status in statuses.keys()
    ]
    for booking in bookings:
        day_of_month = booking.created_at.day
        for status in status_counts:
            if status['status_code'] == booking.status:
                status['counts'][day_of_month - 1] += 1

    booking_summary = {
        'by_status': bookings.values('status').annotate(count=Count('id')),
        'total': bookings.count(),
    }

    for entry in booking_summary['by_status']:
        entry['status_label'] = statuses.get(entry['status'], "Unknown")

    # Call log stats
    tags = dict(CallLog.TAG_CHOICES)
    tag_counts = [
        {
            'tag_code': tag,
            'tag_label': tags[tag],
            'counts': [0] * end_of_month.day  # Initialize counts for each day
        }
        for tag in tags.keys()
    ]
    for call_log in call_logs:
        day_of_month = call_log.call_date.day
        for tag in tag_counts:
            if tag['tag_code'] == call_log.tag.code:
                tag['counts'][day_of_month - 1] += 1

    call_log_summary = {
        'by_tag': call_logs.values('tag__code').annotate(count=Count('id')),
        'by_conversion': call_logs.values('converted').annotate(count=Count('id')),
        'total': call_logs.count(),
    }

    context = {
        'days_in_month': days_in_month,
        'status_counts': status_counts,
        'tag_counts': tag_counts,
        'booking_summary': booking_summary,
        'call_log_summary': call_log_summary,
    }

    return render(request, 'dashboard/agent_dashboard.html', context)
