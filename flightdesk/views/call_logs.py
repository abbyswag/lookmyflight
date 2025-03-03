# CallLog Views
from flightdesk.views import *
from django.db.models import Q
from django.core.paginator import Paginator
from datetime import datetime, timedelta

@login_required


@role_required('supervisor', 'agent', 'cs_team')
def call_log_list(request):
    user = request.user
    is_supervisor = user.groups.filter(name='supervisor').exists()

    # Get filters from request
    search_query = request.GET.get('search', '').strip()
    tag_filter = request.GET.get('tag', '').strip()
    date_filter = request.GET.get('date_filter', '').strip()
    added_by_filter = request.GET.get('added_by', '').strip()

    # Base query
    filters = Q()

    # Search by customer name
    if search_query:
        filters &= Q(name__icontains=search_query)

    # Filter by tag
    if tag_filter:
        filters &= Q(tag__code=tag_filter)

    # Filter by date range
    today = datetime.today().date()
    if date_filter == 'today':
        filters &= Q(call_date__date=today)
    elif date_filter == 'yesterday':
        filters &= Q(call_date__date=today - timedelta(days=1))
    elif date_filter == 'this_week':
        week_start = today - timedelta(days=today.weekday())  # Monday of this week
        filters &= Q(call_date__date__gte=week_start)

    # Supervisor can filter by user who added the call log
    if added_by_filter and is_supervisor:
        filters &= Q(added_by__username=added_by_filter)

    # Fetch call logs with filters applied
    call_logs = CallLog.objects.filter(filters).select_related('tag', 'added_by').order_by('-call_date')

    # Pagination (10 call logs per page)
    paginator = Paginator(call_logs, 100)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Fetch available filters
    tags = Campaign.objects.all()
    users = User.objects.all()

    context = {
        'page_obj': page_obj,
        'tags': tags,
        'users': users,
        'selected_search': search_query,
        'selected_tag': tag_filter,
        'selected_date_filter': date_filter,
        'selected_added_by': added_by_filter,
        'is_supervisor': is_supervisor,
    }

    return render(request, 'call_logs/call_log_list.html', context)


@login_required
def call_log_create(request):
    if request.method == 'POST':
        form = CallLogForm(request.POST)
        if form.is_valid():
            call_log = form.save(commit=False)
            call_log.added_by = request.user
            call_log.save()
            return redirect('call_log_list')
    else:
        form = CallLogForm()
    return render(request, 'call_logs/call_log_form.html', {'form': form})

@login_required
def call_log_detail(request, pk):
    call_log = get_object_or_404(CallLog, pk=pk)
    return render(request, 'call_logs/call_log_detail.html', {'call_log': call_log})

@login_required
def call_log_update(request, pk):
    call_log = get_object_or_404(CallLog, pk=pk)
    if request.method == 'POST':
        form = CallLogForm(request.POST, instance=call_log)
        if form.is_valid():
            form.save()
            return redirect('call_log_detail', pk=pk)
    else:
        form = CallLogForm(instance=call_log)
    return render(request, 'call_logs/call_log_form.html', {'form': form})

@login_required
def call_log_delete(request, pk):
    call_log = get_object_or_404(CallLog, pk=pk)
    if request.method == 'POST':
        call_log.delete()
        return redirect('call_log_list')
    return render(request, 'call_logs/call_log_confirm_delete.html', {'call_log': call_log})

