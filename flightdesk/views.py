from django.shortcuts import render, get_object_or_404
from django.contrib import messages 
from .models import Booking


def approve_booking(request, booking_id):
  booking = get_object_or_404(Booking, booking_id=booking_id)
  booking.status = 'allocating'
  booking.save()
  messages.success(request, 'Booking approved.')
  return render(request, 'approved.html', {
    'mybooking_id': booking_id
  })
