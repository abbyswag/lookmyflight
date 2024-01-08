from django.shortcuts import render, get_object_or_404
from django.contrib import messages 
from .models import BID


def approve_booking(request, bid_id):

  booking = get_object_or_404(BID, bid_id=bid_id)

  booking.status = 'allocating'
  booking.save()
  
  messages.success(request, 'Booking approved.')

  return render(request, 'approved.html', {
    'booking': booking  
  })