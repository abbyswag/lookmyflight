from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from flightdesk.models import Revision, RevisionCategorySetting
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.db.models import Q
from django.conf import settings

from django.core.paginator import Paginator
from flightdesk.forms import RevisionForm
from django.contrib.auth.decorators import user_passes_test


def is_cs_team_or_supervisor(user):
    return user.groups.filter(name__in=['cs_team', 'supervisor']).exists()


@login_required
def revision_list(request):
    # Fetch categories dynamically from the database
    categories = list(RevisionCategorySetting.objects.values_list('category_name', flat=True))

    # Get filters from request
    search_query = request.GET.get('search', '').strip()
    category_filter = request.GET.get('category', '').strip()
    status_filter = request.GET.get('status', '').strip()

    # Base query
    filters = Q(subcategory__in=categories)

    # Search by customer name
    if search_query:
        filters &= Q(booking__call_log__name__icontains=search_query)

    # Filter by category
    if category_filter:
        filters &= Q(subcategory=category_filter)

    # Filter by status
    if status_filter:
        filters &= Q(booking__status=status_filter)

    # Fetch filtered revisions
    revisions = Revision.objects.filter(filters).select_related('booking', 'booking__call_log').order_by('-id')

    paginator = Paginator(revisions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'selected_search': search_query,
        'selected_category': category_filter,
        'selected_status': status_filter,
    }

    return render(request, 'revisions/revision_list.html', context)


@login_required
@user_passes_test(is_cs_team_or_supervisor)
def revision_edit(request, id):
    revision = get_object_or_404(Revision, id=id)
    
    if request.method == "POST":
        form = RevisionForm(request.POST, instance=revision)  # Bind the form with the existing revision
        if form.is_valid():
            form.save()  # Save the updated revision note
            return redirect('revision_list')  # Redirect to the revision list page
    else:
        form = RevisionForm(instance=revision)  # Create a form bound to the existing revision instance

    return render(request, 'revisions/revision_edit.html', {'form': form, 'revision': revision})