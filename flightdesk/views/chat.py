from flightdesk.views import *
from django.http import HttpResponseForbidden
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db.models import Q
from django.db import models
from django.db.models import OuterRef, Subquery


@login_required
def private_chat(request, user_id=None):
    # Determine if the user is a supervisor
    is_supervisor = request.user.groups.filter(name='supervisor').exists()

    # Get the list of users
    users = User.objects.exclude(id=request.user.id)

    # Build dictionaries for unread counts and last unread messages
    unread_data = {}
    for user in users:
        unread_messages = PrivateMessage.objects.filter(
            chat__in=PrivateChat.objects.filter(
                Q(user1=request.user, user2=user) | Q(user1=user, user2=request.user)
            ),
            sender=user,
            read=False
        ).order_by('-timestamp')

        # Get the last unread message and count
        last_unread_message = unread_messages.first()
        unread_count = unread_messages.count()

        # Store the data
        unread_data[user.id] = {
            'last_message': last_unread_message,
            'count': unread_count
        }

    # Get the user to chat with
    user_to_chat = None
    messages = []
    if user_id:
        user_to_chat = get_object_or_404(User, pk=user_id)

        # Get or create the chat
        chat, created = PrivateChat.objects.get_or_create(
            user1=request.user if request.user.id < user_to_chat.id else user_to_chat,
            user2=user_to_chat if request.user.id < user_to_chat.id else request.user,
        )

        # Fetch messages
        messages = PrivateMessage.objects.filter(chat=chat).order_by('-timestamp')

        # Mark all unread messages as read
        PrivateMessage.objects.filter(
            chat=chat,
            read=False,
            sender=user_to_chat,
        ).update(read=True)

        # Handle sending messages
        if request.method == 'POST':
            message_content = request.POST.get('message')
            if message_content:
                PrivateMessage.objects.create(
                    chat=chat, sender=request.user, content=message_content
                )
                return redirect('private_chat', user_id=user_to_chat.id)

    return render(request, 'chat/private_chat_combined.html', {
        'users': users,
        'unread_data': unread_data,
        'user_to_chat': user_to_chat,
        'messages': messages,
        'is_supervisor': is_supervisor
    })


@login_required
def check_for_messages(request):
    # Get all unread messages for the current user
    unread_messages_count = PrivateMessage.objects.filter(
        read=False,
        chat__user1=request.user
    ).count()

    # Return the count of unread messages
    return JsonResponse({'unread_messages': unread_messages_count})


@login_required
def get_chat(request):
    if not request.user.groups.filter(name='supervisor').exists():
        return HttpResponseForbidden("You are not authorized to perform this action.")

    if request.method == 'POST':
        user1_id = request.POST.get('user1_id')
        user2_id = request.POST.get('user2_id')

        # Get the two users
        user1 = get_object_or_404(User, pk=user1_id)
        user2 = get_object_or_404(User, pk=user2_id)

        # Fetch all messages between the two users
        messages = PrivateMessage.objects.filter(
            Q(chat__user1=user1, chat__user2=user2) | Q(chat__user1=user2, chat__user2=user1)
        ).order_by('timestamp')

        # Render the new template for supervisor chat view
        return render(request, 'chat/supervisor_chat_view.html', {
            'messages': messages,
            'chat_title': f"Chat between {user1.username} and {user2.username}",
            'user1': user1,
            'user2': user2,
        })
    else:
        return HttpResponseBadRequest("Invalid request method.")
