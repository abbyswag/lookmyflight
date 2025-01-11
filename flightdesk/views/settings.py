from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from flightdesk.models import Campaign, Query

@login_required
def settings_view(request):
    user = request.user
    is_supervisor = user.groups.filter(name='supervisor').exists()

    tags = Campaign.objects.all()
    query_types = Query.objects.all()

    context = {
        'is_supervisor': is_supervisor,
        'tags': tags,
        'query_types': query_types,
    }

    return render(request, 'crm/settings.html', context)
