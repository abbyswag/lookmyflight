# views.py
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.http import HttpResponseRedirect
from .models import Booking
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

class BookingApprovalView(View):
    def get(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Perform your approval logic here, and update the status
        booking.status = 'approved'
        booking.save()

        # Redirect to a success page or any other appropriate page
        return HttpResponseRedirect('/success/')  # Change the URL as needed

class SaveImageView(View):
    @csrf_exempt
    def post(self, request):
        if request.method == 'POST':
            try:
                image_data = request.POST.get('image_data')
                instance_id = request.POST.get('instance_id')

                # Retrieve the model instance
                your_model_instance = Booking.objects.get(pk=instance_id)

                # Save the image_data to the 'ticket_image' field
                your_model_instance.ticket_image = image_data
                your_model_instance.save()

                return JsonResponse({'status': 'success'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})

        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})