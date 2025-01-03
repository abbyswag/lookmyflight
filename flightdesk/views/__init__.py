from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404

from flightdesk.models import Airline, CallLog, Booking, Campaign, Query, PrivateChat, PrivateMessage
from flightdesk.forms import AirlineForm, RevisionForm

# Check for Supervisor Group
def is_supervisor(user):
    return user.groups.filter(name='supervisor').exists()