import openpyxl
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
import requests
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
    context = {
        'is_supervisor': is_supervisor,
    }
    return render(request, 'dashboard/admin_dashboard.html', context)


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


from django.http import JsonResponse
from django.db.models import Sum, Value
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import TruncDate

# Helper function to get date range based on the time filter
def get_date_range(time_filter):
    today = timezone.now().date()
    
    if time_filter == 'thisMonth':
        start_date = today.replace(day=1)
        end_date = today
    elif time_filter == 'thisWeek':
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    elif time_filter == 'lastMonth':
        start_date = today.replace(day=1) - timedelta(days=1)
        start_date = start_date.replace(day=1)
        end_date = start_date.replace(day=28)  # last day of last month
    elif time_filter == 'thisQuarter':
        quarter = (today.month - 1) // 3 + 1
        start_date = today.replace(month=(quarter - 1) * 3 + 1, day=1)
        end_date = today
    else:
        start_date = today
        end_date = today
    
    return start_date, end_date

# View to fetch MCO data by filter and time range
def fetch_mco_data(request):
    filter_type = request.GET.get('filter', 'call_log_tag')
    time_filter = request.GET.get('time_filter', 'thisMonth')

    start_date, end_date = get_date_range(time_filter)
    
    bookings = Booking.objects.filter(created_at__range=[start_date, end_date])

    if filter_type == 'status':
        data = bookings.values('status').annotate(total_mco=Sum('mco')).order_by('status')
        labels = [item['status'] for item in data]
        mco_values = [item['total_mco'] for item in data]
    
    elif filter_type == 'agents':
        data = bookings.values('added_by__username').annotate(total_mco=Sum('mco')).order_by('added_by__username')
        labels = [item['added_by__username'] for item in data]
        mco_values = [item['total_mco'] for item in data]
    
    elif filter_type == 'call_log_tag':
        data = bookings.filter(call_log__isnull=False).values('call_log__tag__code').annotate(total_mco=Sum('mco')).order_by('call_log__tag__code')
        labels = [item['call_log__tag__code'] for item in data]
        mco_values = [item['total_mco'] for item in data]
    
    elif filter_type == 'category':
        # Define the categories we want to track
        categories = ['flight', 'hotel', 'vehicle']
        
        # Create a Case/When expression to categorize bookings
        from django.db.models import Case, When, CharField
        
        data = bookings.annotate(
            category=Case(
                *[When(subcategory__icontains=cat, then=Value(cat.capitalize())) for cat in categories],
                default=Value('Other'),
                output_field=CharField(),
            )
        ).values('category').annotate(
            total_mco=Sum('mco')
        ).exclude(category='Other').order_by('category')
        
        labels = [item['category'] for item in data]
        mco_values = [item['total_mco'] for item in data]
    
    else:
        return JsonResponse({'error': 'Invalid filter type'}, status=400)

    return JsonResponse({
        'labels': labels,
        'mco_values': mco_values,
    })


def fetch_bookings_and_passengers(request):
    time_filter = request.GET.get('time_filter', 'thisMonth')
    tag_filter = request.GET.get('tag', '')

    start_date, end_date = get_date_range(time_filter)
    
    # Start with base booking query
    bookings = Booking.objects.filter(created_at__range=[start_date, end_date])

    # Apply tag filter if provided
    if tag_filter:
        bookings = bookings.filter(call_log__tag__code=tag_filter)

    # Aggregate data by date
    daily_data = (bookings
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(
            booking_count=Count('id', distinct=True),
            passenger_count=Count('passenger', distinct=True)
        )
        .order_by('date'))

    # Prepare data for the chart
    dates = []
    booking_counts = []
    passenger_counts = []

    # Fill in any missing dates with zero counts
    current_date = start_date
    data_dict = {item['date']: item for item in daily_data}
    
    while current_date <= end_date:
        dates.append(current_date.strftime('%Y-%m-%d'))
        if current_date in data_dict:
            booking_counts.append(data_dict[current_date]['booking_count'])
            passenger_counts.append(data_dict[current_date]['passenger_count'])
        else:
            booking_counts.append(0)
            passenger_counts.append(0)
        current_date += timedelta(days=1)

    return JsonResponse({
        'dates': dates,
        'booking_counts': booking_counts,
        'passenger_counts': passenger_counts
    })


def fetch_call_log_data(request):
    filter_type = request.GET.get('filter', 'tag')
    time_filter = request.GET.get('time_filter', 'thisMonth')

    start_date, end_date = get_date_range(time_filter)
    
    call_logs = CallLog.objects.filter(call_date__range=[start_date, end_date])

    if filter_type == 'tag':
        data = (call_logs.filter(tag__isnull=False)
                .values('tag__code')
                .annotate(count=Count('id'))
                .order_by('tag__code'))
        labels = [item['tag__code'] for item in data]
        values = [item['count'] for item in data]
    
    elif filter_type == 'query':
        data = (call_logs.filter(query_type__isnull=False)
                .values('query_type__code') 
                .annotate(count=Count('id'))
                .order_by('query_type__code'))
        labels = [item['query_type__code'] for item in data]
        values = [item['count'] for item in data]
    
    elif filter_type == 'agent':
        data = (call_logs.filter(added_by__isnull=False)
                .values('added_by__username')
                .annotate(count=Count('id'))
                .order_by('added_by__username'))
        labels = [item['added_by__username'] for item in data]
        values = [item['count'] for item in data]
    
    else:
        return JsonResponse({'error': 'Invalid filter type'}, status=400)

    return JsonResponse({
        'labels': labels,
        'values': values,
    })


def geocode_zip(zip_code):
    """Geocode a zip code using Google Maps API"""
    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={zip_code}&key={settings.GOOGLE_MAPS_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if data['status'] == 'OK':
            location = data['results'][0]['geometry']['location']
            return location['lat'], location['lng']
        return None, None
    except Exception as e:
        print(f"Geocoding error for {zip_code}: {str(e)}")
        return None, None

def fetch_booking_locations(request):
    time_filter = request.GET.get('time_filter', 'thisMonth')
    start_date, end_date = get_date_range(time_filter)
    
    # Get bookings within date range with related billing info and call log
    bookings = (Booking.objects
                .filter(created_at__range=[start_date, end_date])
                .select_related('billinginformation', 'call_log__tag'))

    location_data = []
    # Cache for zip codes to avoid repeated API calls within the same request
    zip_cache = {}
    
    for booking in bookings:
        try:
            if not booking.billinginformation or not booking.billinginformation.zipcode:
                continue
                
            zip_code = booking.billinginformation.zipcode
            
            # Check cache first
            if zip_code in zip_cache:
                lat, lng = zip_cache[zip_code]
            else:
                # Geocode and cache the result
                lat, lng = geocode_zip(zip_code)
                zip_cache[zip_code] = (lat, lng)
            
            if lat and lng:
                location_data.append({
                    'lat': lat,
                    'lng': lng,
                    'tag': booking.call_log.tag.code if booking.call_log and booking.call_log.tag else 'Other',
                    'zipcode': zip_code
                })
                
        except Exception as e:
            print(f"Error processing booking {booking.id}: {str(e)}")
            continue

    return JsonResponse({
        'locations': location_data
    })