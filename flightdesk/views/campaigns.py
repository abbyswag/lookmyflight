from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from flightdesk.views import *

# Helper function to restrict access to supervisors only
def is_supervisor(user):
    return user.groups.filter(name='supervisor').exists()

@login_required
@user_passes_test(is_supervisor)
def campaign_list(request):
    """ Display all campaigns """
    campaigns = CampaignModel.objects.all().order_by('-created_at')
    return render(request, 'campaigns/campaign_list.html', {'campaigns': campaigns})


@login_required
@user_passes_test(is_supervisor)
def campaign_create(request):
    """ Create a new campaign """
    if request.method == "POST":
        form = CampaignModelForm(request.POST)
        if form.is_valid():
            campaign = form.save(commit=False)
            campaign.created_by = request.user
            campaign.save()
            messages.success(request, "CampaignModel created successfully!")
            return redirect('campaign_list')
    else:
        form = CampaignModelForm()
    return render(request, 'campaigns/campaign_form.html', {'form': form, 'action': 'Create'})


@login_required
@user_passes_test(is_supervisor)
def campaign_update(request, campaign_id):
    """ Update an existing campaign """
    campaign = get_object_or_404(CampaignModel, id=campaign_id)

    if request.method == "POST":
        form = CampaignModelForm(request.POST, instance=campaign)
        if form.is_valid():
            form.save()
            messages.success(request, "CampaignModel updated successfully!")
            return redirect('camp_model_list')

    else:
        form = CampaignModelForm(instance=campaign)
    
    return render(request, 'campaigns/campaign_form.html', {'form': form, 'action': 'Update'})


@login_required
@user_passes_test(is_supervisor)
def campaign_delete(request, campaign_id):
    """ Delete a campaign """
    campaign = get_object_or_404(CampaignModel, id=campaign_id)

    if request.method == "POST":
        campaign.delete()
        messages.success(request, "CampaignModel deleted successfully!")
        return redirect('camp_model_list')

    return render(request, 'campaigns/campaign_confirm_delete.html', {'campaign': campaign})
