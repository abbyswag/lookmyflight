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
