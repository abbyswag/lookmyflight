from flightdesk.views import *


# Airline Views (Supervisor only)
@login_required
@user_passes_test(is_supervisor)
def airline_list(request):
    airlines = Airline.objects.all()
    return render(request, 'crm/airline_list.html', {'airlines': airlines})

@login_required
@user_passes_test(is_supervisor)
def airline_create(request):
    if request.method == 'POST':
        form = AirlineForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('airline_list')
    else:
        form = AirlineForm()
    return render(request, 'crm/airline_form.html', {'form': form})

@login_required
@user_passes_test(is_supervisor)
def airline_detail(request, pk):
    airline = get_object_or_404(Airline, pk=pk)
    return render(request, 'crm/airline_detail.html', {'airline': airline})

@login_required
@user_passes_test(is_supervisor)
def airline_update(request, pk):
    airline = get_object_or_404(Airline, pk=pk)
    if request.method == 'POST':
        form = AirlineForm(request.POST, instance=airline)
        if form.is_valid():
            form.save()
            return redirect('airline_detail', pk=pk)
    else:
        form = AirlineForm(instance=airline)
    return render(request, 'crm/airline_form.html', {'form': form})

@login_required
@user_passes_test(is_supervisor)
def airline_delete(request, pk):
    airline = get_object_or_404(Airline, pk=pk)
    if request.method == 'POST':
        airline.delete()
        return redirect('crm/airline_list')
    return render(request, 'crm/airline_confirm_delete.html', {'airline': airline})