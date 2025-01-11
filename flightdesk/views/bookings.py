from django.core.paginator import Paginator
from django.db.models import Q
from datetime import datetime, timedelta
from flightdesk.views import *


@login_required
def booking_list(request):
    # Get all bookings
    if is_agent(request.user):
        bookings = Booking.objects.filter(added_by=request.user).order_by('-created_at')
    else:
        bookings = Booking.objects.all().order_by('-created_at')

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        bookings = bookings.filter(Q(call_log__name__icontains=search_query) | Q(booking_id__icontains=search_query))

    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        bookings = bookings.filter(status=status_filter)

    # Filter by date range
    date_filter = request.GET.get('date_filter', '')
    if date_filter == 'last_week':
        last_week = datetime.now() - timedelta(days=7)
        bookings = bookings.filter(created_at__gte=last_week)
    elif date_filter == 'last_month':
        last_month = datetime.now() - timedelta(days=30)
        bookings = bookings.filter(created_at__gte=last_month)
    else:
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        if start_date and end_date:
            bookings = bookings.filter(created_at__range=[start_date, end_date])

    # Pagination
    paginator = Paginator(bookings, 100)  # Show 100 bookings per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'bookings/booking_list.html', {
        'bookings': page_obj,
        'is_supervisor': is_supervisor(request.user),
        'search_query': search_query,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'start_date': request.GET.get('start_date', ''),
        'end_date': request.GET.get('end_date', ''),
    })
