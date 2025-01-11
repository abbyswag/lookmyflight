from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404

from flightdesk.models import Airline, CallLog, Booking, Campaign, Query, PrivateChat, PrivateMessage, RevisionCategorySetting
from flightdesk.forms import AirlineForm, RevisionForm, RevisionCategoryForm

# Check for Supervisor Group
def is_supervisor(user):
    return user.groups.filter(name='supervisor').exists()

# Check for Supervisor Group
def is_agent(user):
    return user.groups.filter(name='agent').exists()