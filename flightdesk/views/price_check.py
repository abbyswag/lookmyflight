import requests
from django.shortcuts import render


def price_check(request):
    # Check if access token is available in the session (or browser storage in frontend)
    access_token = request.session.get('access_token')

    if not access_token:
        # If no token is found, request a new one from Amadeus API
        client_id = 'your_api_key_here'
        client_secret = 'your_api_secret_here'
        url = 'https://test.api.amadeus.com/v1/security/oauth2/token'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
        response = requests.post(url, headers=headers, data=data)
        response_data = response.json()

        # Save the access token and expiry time in session
        access_token = response_data['access_token']
        expires_in = response_data['expires_in']
        request.session['access_token'] = access_token
        request.session['expires_in'] = expires_in

    return render(request, 'price_check.html', {'access_token': access_token})