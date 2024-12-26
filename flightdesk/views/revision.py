from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from flightdesk.models import Revision
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.conf import settings
from flightdesk.forms import RevisionForm


@login_required
def revision_list(request):
    # Filter revisions for cancelled and refund bookings
    revisions = Revision.objects.filter(subcategory__in=['cancelled', 'refund'])
    
    return render(request, 'crm/revision_list.html', {'revisions': revisions})


@login_required
def revision_edit(request, id):
    revision = get_object_or_404(Revision, id=id)
    
    if request.method == "POST":
        form = RevisionForm(request.POST, instance=revision)  # Bind the form with the existing revision
        if form.is_valid():
            form.save()  # Save the updated revision note
            return redirect('revision_list')  # Redirect to the revision list page
    else:
        form = RevisionForm(instance=revision)  # Create a form bound to the existing revision instance

    return render(request, 'crm/revision_edit.html', {'form': form, 'revision': revision})