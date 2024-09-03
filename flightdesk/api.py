from django.http import JsonResponse
from django.db.models import Q
from .models import CallLog, Booking, BillingInformation, Passenger
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
import json
from datetime import datetime
from django.core.files.base import ContentFile
import base64

def search_customers(request):
    search_term = request.GET.get('term', '')
    if len(search_term) < 3:
        return JsonResponse([], safe=False)

    customers = CallLog.objects.filter(
        Q(name__icontains=search_term) | Q(phone__icontains=search_term)
    ).values('id', 'name', 'phone', 'email')[:10]  # Limit to 10 results

    return JsonResponse(list(customers), safe=False)

@login_required
@require_http_methods(["POST"])
def create_booking(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
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
                    image_data = image_data[0].split(',')[1]  # Remove the data:image/png;base64, part
                    image = ContentFile(base64.b64decode(image_data), name=f"{field}.png")
                    setattr(booking, field, image)

            save_images(data.get('flight_info_img'), 'flight_info_img')
            save_images(data.get('hotel_info_img'), 'hotel_info_img')
            save_images(data.get('vehicle_info_img'), 'vehicle_info_img')
            
            booking.save()
            return JsonResponse({'success': True, 'booking_id': booking.booking_id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})