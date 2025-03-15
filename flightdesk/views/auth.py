from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.http import JsonResponse
from django.conf import settings
import random
from django.core.mail import EmailMessage
from django.core.mail.backends.smtp import EmailBackend
import threading

from django.contrib.auth.models import User

# Store OTP in session
def generate_otp():
    return random.randint(1000, 9999)


def send_otp_email(email, otp, username):
    # Create a function to be executed in a separate thread
    def send_mail_task():
        try:
            subject = f"OTP for {username}"
            message = f"OTP for {username} is: {otp}. Please enter this to complete your login."
            from_email = "dualnature67@gmail.com"

            email_backend = EmailBackend(
                host=settings.EMAIL_HOST,
                port=settings.EMAIL_PORT,
                username=settings.SECONDARY_EMAIL_CONFIG['EMAIL_HOST_USER'],
                password=settings.SECONDARY_EMAIL_CONFIG['EMAIL_HOST_PASSWORD'],
                use_tls=settings.EMAIL_USE_TLS,
            )
            email_message = EmailMessage(subject, message, from_email, [email], connection=email_backend)
            email_message.send()
            print(f"OTP email sent successfully to {email}")
        except Exception as e:
            print(f"Error sending OTP email: {e}")
    
    # Start email sending in a separate thread
    email_thread = threading.Thread(target=send_mail_task)
    email_thread.daemon = True
    email_thread.start()


def login_view(request):
    if request.method == 'POST':
        if 'otp' in request.POST:
            # Step 3: Verify OTP
            entered_otp = request.POST['otp']
            stored_otp = request.session.get('otp')
            if str(entered_otp) == str(stored_otp):
                # OTP verified, log in the user
                user_id = request.session.get('otp_user_id')
                user = User.objects.get(pk=user_id)
                login(request, user)
                # Clear OTP and user_id from session
                del request.session['otp']
                del request.session['otp_user_id']
                return redirect('dashboard')
            else:
                return render(request, 'crm/otp.html', {'error': 'Invalid OTP'})
        else:
            # Step 1: Authenticate user credentials
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # Generate OTP and send email
                otp = generate_otp()
                request.session['otp'] = otp
                request.session['otp_user_id'] = user.id
                
                # Send OTP email asynchronously
                send_otp_email('support@lookmyflight.com', otp, username)
                
                # Step 2: Show OTP form
                return render(request, 'crm/otp.html', {'email': 'support@lookmyflight.com'})
            else:
                return render(request, 'crm/login.html', {'error': 'Invalid credentials'})
    return render(request, 'crm/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')