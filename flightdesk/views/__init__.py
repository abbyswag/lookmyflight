from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User

from flightdesk.models import Airline, CallLog, Booking, Campaign, Query, PrivateChat, PrivateMessage, RevisionCategorySetting, CampaignModel
from flightdesk.forms import AirlineForm, RevisionForm, RevisionCategoryForm, CallLogForm, BookingForm, CampaignForm, QueryForm, CampaignModelForm

# Check for Supervisor Group
def is_supervisor(user):
    return user.groups.filter(name='supervisor').exists()

# Check for Supervisor Group
def is_agent(user):
    return user.groups.filter(name='agent').exists()


def role_required(*allowed_roles):
    """
    Decorator for views that checks whether a user
    belongs to any of the allowed roles (groups).
    """
    def decorator(view_func):
        @login_required  # Ensures user is logged in before checking roles
        def _wrapped_view(request, *args, **kwargs):
            # Check if the user is in any of the allowed groups
            if request.user.groups.filter(name__in=allowed_roles).exists():
                return view_func(request, *args, **kwargs)
            else:
                # If user is not in the allowed roles, raise a 403 error or redirect
                return redirect('forbidden_page')
        return _wrapped_view
    return decorator