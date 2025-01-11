from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from flightdesk.models import Revision, RevisionCategorySetting
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.conf import settings
from flightdesk.forms import RevisionForm
from django.contrib.auth.decorators import user_passes_test


def is_cs_team_or_supervisor(user):
    return user.groups.filter(name__in=['cs_team', 'supervisor']).exists()

@login_required
def revision_list(request):
    # Fetch the categories dynamically from the database
    categories = RevisionCategorySetting.objects.values_list('category_name', flat=True)
    print(categories)
    
    # Filter revisions based on the fetched categories
    revisions = Revision.objects.filter(subcategory__in=categories)
    
    return render(request, 'crm/revision_list.html', {'revisions': revisions})


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

    return render(request, 'crm/revision_edit.html', {'form': form, 'revision': revision})