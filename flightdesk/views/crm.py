from django.shortcuts import render


def forbidden_view(request):
    """A simple view to render a 403 Forbidden page."""
    return render(request, 'crm/forbidden.html', status=403)