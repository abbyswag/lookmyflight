from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden, JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth.models import User
from flightdesk.models import PrivateChat, PrivateMessage

@login_required
def private_chat(request, user_id=None):
    # Check if user is a supervisor
    is_supervisor = request.user.groups.filter(name='supervisor').exists()

    # Get all users except the current user
    users = User.objects.exclude(id=request.user.id)

    # Dictionary to store unread messages data
    unread_data = {}
    for user in users:
        unread_messages = PrivateMessage.objects.filter(
            chat__in=PrivateChat.objects.filter(
                Q(user1=request.user, user2=user) | Q(user1=user, user2=request.user)
            ),
            sender=user,
            read=False
        ).order_by('-timestamp')

        # Get the last message (unread or read)
        last_message = PrivateMessage.objects.filter(
            chat__in=PrivateChat.objects.filter(
                Q(user1=request.user, user2=user) | Q(user1=user, user2=request.user)
            )
        ).order_by('-timestamp').first()

        # Store data (count and last message content)
        unread_data[user.id] = {
            'last_message': last_message.content if last_message else "No messages yet",
            'count': unread_messages.count()
        }

    # Sort users by unread message count (most unread at the top)
    users = sorted(users, key=lambda u: unread_data[u.id]['count'], reverse=True)

    # Get the selected chat
    user_to_chat = None
    messages = []
    if user_id:
        user_to_chat = get_object_or_404(User, pk=user_id)

        # Get or create the chat
        chat, created = PrivateChat.objects.get_or_create(
            user1=request.user if request.user.id < user_to_chat.id else user_to_chat,
            user2=user_to_chat if request.user.id < user_to_chat.id else request.user,
        )

        # Fetch chat messages
        messages = PrivateMessage.objects.filter(chat=chat).order_by('-timestamp')

        # Mark unread messages as read
        PrivateMessage.objects.filter(chat=chat, read=False, sender=user_to_chat).update(read=True)

        # Handle new messages
        if request.method == 'POST':
            message_content = request.POST.get('message')
            if message_content:
                new_message = PrivateMessage.objects.create(
                    chat=chat, sender=request.user, content=message_content
                )

                # # Mark the new message as unread for the recipient
                # chat.user1_unread = chat.user1_unread + 1 if chat.user1 == user_to_chat else chat.user1_unread
                # chat.user2_unread = chat.user2_unread + 1 if chat.user2 == user_to_chat else chat.user2_unread
                chat.save()

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
    """ Returns the count of unread messages for the current user """
    unread_messages_count = PrivateMessage.objects.filter(
        read=False,
        chat__in=PrivateChat.objects.filter(Q(user1=request.user))
    ).count()

    return JsonResponse({'unread_messages': unread_messages_count})


@login_required
def get_chat(request):
    """ Allows supervisors to fetch messages between two users """
    if not request.user.groups.filter(name='supervisor').exists():
        return HttpResponseForbidden("You are not authorized to perform this action.")

    if request.method == 'POST':
        user1_id = request.POST.get('user1_id')
        user2_id = request.POST.get('user2_id')

        # Get the two users
        user1 = get_object_or_404(User, pk=user1_id)
        user2 = get_object_or_404(User, pk=user2_id)

        # Fetch messages between the two users
        messages = PrivateMessage.objects.filter(
            Q(chat__user1=user1, chat__user2=user2) | Q(chat__user1=user2, chat__user2=user1)
        ).order_by('timestamp')

        return render(request, 'chat/supervisor_chat_view.html', {
            'messages': messages,
            'chat_title': f"Chat between {user1.username} and {user2.username}",
            'user1': user1,
            'user2': user2,
        })

    return HttpResponseBadRequest("Invalid request method.")
