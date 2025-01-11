from django.http import JsonResponse
from django.db.models import Q
from .models import CallLog, Booking, BillingInformation, Passenger, Campaign, Query
from django.views.decorators.http import require_http_methods, require_GET
from django.contrib.auth.decorators import login_required
import json
from datetime import datetime
from django.core.files.base import ContentFile
import base64
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
import re

@login_required
def search_customers(request):
    search_term = request.GET.get('term', '')
    if len(search_term) < 3:
        return JsonResponse([], safe=False)

    customers = CallLog.objects.filter(
        Q(name__icontains=search_term) | Q(phone__icontains=search_term)
    ).values('id', 'name', 'phone', 'call_date')[:10]  # Limit to 10 results

    return JsonResponse(list(customers), safe=False)

@login_required
@require_http_methods(["POST"])
def create_booking(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            # Ensure at least one of the checkboxes is True
            if not any([data.get('regarding_flight', False), data.get('regarding_hotel', False), data.get('regarding_vehicle', False)]):
                return JsonResponse({'success': False, 'error': 'At least one of "regarding_flight", "regarding_hotel", or "regarding_vehicle" must be True.'})

            call_log = CallLog.objects.get(id=data['call_log'])
            booking = Booking.objects.create(
                added_by=request.user,
                status='initiated',
                mco=data['mco'],
                currency=data['currency'],
                regarding_flight=data['regarding_flight'],
                regarding_hotel=data['regarding_hotel'],
                regarding_vehicle=data['regarding_vehicle'],
                subcategory=data['subcategory'],
                call_log=call_log
            )
            return JsonResponse({'success': True, 'booking_id': booking.booking_id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@require_http_methods(["POST"])
def add_billing_info(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            # Validate input fields
            required_fields = [
                'booking_id', 'card_type', 'card_holder_name', 'card_holder_number', 
                'email', 'card_number', 'expiry_date', 'card_cvv', 
                'primary_address', 'country', 'zipcode'
            ]
            
            # Check for blank fields
            for field in required_fields:
                if field not in data or not data[field].strip():
                    return JsonResponse({'success': False, 'error': f"{field.replace('_', ' ').capitalize()} is required and cannot be blank."})
            
            # Validate card number length (15 or 16 digits)
            if not re.match(r'^\d{15,16}$', data['card_number']):
                return JsonResponse({'success': False, 'error': 'Card number must be 15 or 16 digits long.'})
            
            # Validate CVV (3 or 4 digits)
            if not re.match(r'^\d{3,4}$', data['card_cvv']):
                return JsonResponse({'success': False, 'error': 'CVV must be 3 or 4 digits long.'})
            
            # Validate card holder name (should not contain numbers)
            if re.search(r'\d', data['card_holder_name']):
                return JsonResponse({'success': False, 'error': 'Card holder name must not contain numbers.'})
            
            # Validate email format
            if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', data['email']):
                return JsonResponse({'success': False, 'error': 'Invalid email format.'})
            
            # Validate expiry date (MM/YY or MM/YYYY)
            if not re.match(r'^(0[1-9]|1[0-2])\/?([0-9]{2}|[0-9]{4})$', data['expiry_date']):
                return JsonResponse({'success': False, 'error': 'Invalid expiry date format. Use MM/YY or MM/YYYY.'})

            # Validate zip code (you can adjust this based on your country’s zip code format)
            if not re.match(r'^\d{5}(-\d{4})?$|^\d{6}$', data['zipcode']):
                return JsonResponse({'success': False, 'error': 'Invalid zipcode format.'})
            

            booking = Booking.objects.get(booking_id=data['booking_id'])
            billing_info = BillingInformation.objects.create(
                booking=booking,
                card_type=data['card_type'],
                card_holder_name=data['card_holder_name'],
                card_holder_number=data['card_holder_number'],
                email=data['email'],
                card_number=data['card_number'],
                expiry_date=data['expiry_date'],
                card_cvv=data['card_cvv'],
                primary_address=data['primary_address'],
                country=data['country'],
                zipcode=data['zipcode']
            )
            return JsonResponse({'success': True, 'billing_id': billing_info.id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@require_http_methods(["POST"])
def add_passengers(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            booking = Booking.objects.get(booking_id=data['booking_id'])
            passengers = data['passengers']
            
            for passenger_data in passengers:
                required_fields = ['full_passenger_name', 'date_of_birth', 'gender']
                
                for field in required_fields:
                    if not passenger_data.get(field) or not passenger_data[field].strip():
                        return JsonResponse({'success': False, 'error': f"{field.replace('_', ' ').capitalize()} is required and cannot be blank."})
                    
                Passenger.objects.create(
                    booking=booking,
                    full_passenger_name=passenger_data['full_passenger_name'],
                    date_of_birth=datetime.strptime(passenger_data['date_of_birth'], '%Y-%m-%d').date(),
                    gender=passenger_data['gender'],
                    ticket_number=passenger_data.get('ticket_number', '')
                )
            
            return JsonResponse({'success': True, 'message': 'Passengers added successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@require_http_methods(["POST"])
def save_booking(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            booking = Booking.objects.get(booking_id=data['booking_id'])
            
            def save_images(image_data, field):
                if image_data:
                    image_data = image_data[0].split(',')[1] 
                    image = ContentFile(base64.b64decode(image_data), name=f"{field}.png")
                    setattr(booking, field, image)

            # Validate and save flight-related information if applicable
            if booking.regarding_flight:
                if 'flight_cost' not in data or 'flight_info_img' not in data:
                    return JsonResponse({'success': False, 'error': 'Flight cost and flight info image are required when regarding_flight is True.'})
                try:
                    booking.flight_cost = float(data.get('flight_cost', 0))
                except ValueError:
                    return JsonResponse({'success': False, 'error': 'Invalid flight cost.'})
                save_images(data.get('flight_info_img'), 'flight_info_img')

            # Validate and save hotel-related information if applicable
            if booking.regarding_hotel:
                if 'hotel_cost' not in data or 'hotel_info_img' not in data:
                    return JsonResponse({'success': False, 'error': 'Hotel cost and hotel info image are required when regarding_hotel is True.'})
                try:
                    booking.hotel_cost = float(data.get('hotel_cost', 0))
                except ValueError:
                    return JsonResponse({'success': False, 'error': 'Invalid hotel cost.'})
                save_images(data.get('hotel_info_img'), 'hotel_info_img')

            # Validate and save vehicle-related information if applicable
            if booking.regarding_vehicle:
                if 'vehicle_cost' not in data or 'vehicle_info_img' not in data:
                    return JsonResponse({'success': False, 'error': 'Vehicle cost and vehicle info image are required when regarding_vehicle is True.'})
                try:
                    booking.vehicle_cost = float(data.get('vehicle_cost', 0))
                except ValueError:
                    return JsonResponse({'success': False, 'error': 'Invalid vehicle cost.'})
                save_images(data.get('vehicle_info_img'), 'vehicle_info_img')
            
            booking.save()
            return JsonResponse({'success': True, 'booking_id': booking.booking_id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@require_GET
def call_log_summary_api(request):
    filter_type = request.GET.get('filter', 'today')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    today = timezone.now().date()
    if filter_type == 'today':
        start_date = today
        end_date = today
    elif filter_type == 'lastWeek':
        start_date = today - timedelta(days=7)
        end_date = today
    elif filter_type == 'lastMonth':
        start_date = today - timedelta(days=30)
        end_date = today
    elif filter_type == 'custom':
        start_date = timezone.datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = timezone.datetime.strptime(end_date, "%Y-%m-%d").date()

    tags = Campaign.objects.all()
    query_types = Query.objects.all()

    call_logs = CallLog.objects.filter(call_date__date__range=[start_date, end_date])

    call_log_counts = {}
    for tag in tags:
        call_log_counts[tag.code] = {}
        for query_type in query_types:
            count = call_logs.filter(tag=tag, query_type=query_type).count()
            call_log_counts[tag.code][query_type.code] = count
        call_log_counts[tag.code]['total'] = sum(call_log_counts[tag.code].values())

    return JsonResponse({
        'call_log_counts': call_log_counts,
        'tags': [tag.code for tag in tags],
        'query_types': [query_type.code for query_type in query_types],
    })


@require_GET
@login_required
def call_log_bar_chart_api(request):
    filter_type = request.GET.get('filter', 'today')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    today = now().date()
    if filter_type == 'today':
        start_date = today
        end_date = today
    elif filter_type == 'lastWeek':
        start_date = today - timedelta(days=7)
        end_date = today
    elif filter_type == 'lastMonth':
        start_date = today - timedelta(days=30)
        end_date = today
    elif filter_type == 'custom' and start_date and end_date:
        start_date = now().strptime(start_date, "%Y-%m-%d").date()
        end_date = now().strptime(end_date, "%Y-%m-%d").date()

    # Get all call logs within the specified range
    call_logs = CallLog.objects.filter(call_date__date__range=[start_date, end_date])

    # Aggregate data by tag
    tag_data = (
        call_logs.values('tag__code')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # Aggregate data by query type
    query_type_data = (
        call_logs.values('query_type__code')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    response_data = {
        'tags': list(tag_data),
        'query_types': list(query_type_data),
    }

    return JsonResponse(response_data)



# Bookings API
@require_GET
@login_required
def booking_summary_api(request):
    filter_type = request.GET.get('filter', 'today')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    tag = request.GET.get('tag')
    query_type = request.GET.get('query_type')

    today = timezone.now().date()
    if filter_type == 'today':
        start_date = today
        end_date = today
    elif filter_type == 'lastWeek':
        start_date = today - timedelta(days=7)
        end_date = today
    elif filter_type == 'lastMonth':
        start_date = today - timedelta(days=30)
        end_date = today
    elif filter_type == 'custom':
        start_date = timezone.datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = timezone.datetime.strptime(end_date, "%Y-%m-%d").date()

    bookings = Booking.objects.filter(created_at__date__range=[start_date, end_date])

    if tag:
        bookings = bookings.filter(call_log__tag__code=tag)
    if query_type:
        bookings = bookings.filter(call_log__query_type__code=query_type)

    summary = (
        bookings.values('added_by__username')
        .annotate(
            num_bookings=Count('id'),
            num_passengers=Count('passenger'),
            revenue=Sum('mco')
        )
        .order_by('-num_bookings')
    )

    result = [
        {
            'agent': item['added_by__username'],
            'num_bookings': item['num_bookings'],
            'num_passengers': item['num_passengers'],
            'revenue': float(item['revenue']) if item['revenue'] else 0
        }
        for item in summary
    ]

    return JsonResponse(result, safe=False)


from django.utils.timezone import now


@require_GET
@login_required
def booking_daily_chart_api(request):
    filter_type = request.GET.get('filter', 'today')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    today = now().date()
    if filter_type == 'today':
        start_date = today
        end_date = today
    elif filter_type == 'lastWeek':
        start_date = today - timedelta(days=7)
        end_date = today
    elif filter_type == 'lastMonth':
        start_date = today - timedelta(days=30)
        end_date = today
    elif filter_type == 'custom' and start_date and end_date:
        start_date = now().strptime(start_date, "%Y-%m-%d").date()
        end_date = now().strptime(end_date, "%Y-%m-%d").date()

    # Get all bookings within the specified range
    bookings = Booking.objects.filter(created_at__date__range=[start_date, end_date])

    # Initialize data
    date_range = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
    data = {
        'dates': [date.strftime("%Y-%m-%d") for date in date_range],
        'daily_bookings': [],
        'daily_passengers': [],
        'daily_revenue': [],
    }

    # Aggregate data for each date
    for date in date_range:
        day_bookings = bookings.filter(created_at__date=date)
        daily_booking_count = day_bookings.count()
        daily_passenger_count = day_bookings.aggregate(count=Count('passenger'))['count'] or 0
        daily_revenue = day_bookings.aggregate(total=Sum('mco'))['total'] or 0

        data['daily_bookings'].append(daily_booking_count)
        data['daily_passengers'].append(daily_passenger_count)
        data['daily_revenue'].append(float(daily_revenue))  # Ensure JSON serializable

    return JsonResponse(data)



from django.db.models import Sum, Count
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

@login_required
def customer_heatmap_api(request):
    # Aggregate data by zipcode
    data = (
        BillingInformation.objects.values('zipcode')
        .annotate(
            total_revenue=Sum('booking__mco'),
            total_bookings=Count('booking'),
            total_passengers=Sum('booking__passenger__id'),  # Adjust based on Passenger model relation
        )
        .exclude(zipcode=None)  # Exclude entries with missing zipcodes
        .order_by('-total_revenue')
    )

    # Prepare heatmap data
    heatmap_data = []
    for item in data:
        heatmap_data.append({
            'zipcode': item['zipcode'],
            'total_revenue': item['total_revenue'],
            'total_bookings': item['total_bookings'],
            'total_passengers': item['total_passengers'],
        })

    # Top 5 zipcodes for the summary table
    top_locations = heatmap_data[:5]

    return JsonResponse({
        'heatmap_data': heatmap_data,
        'top_locations': top_locations,
    })
