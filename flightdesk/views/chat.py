from flightdesk.views import *
from django.http import HttpResponseForbidden
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db.models import Q


@login_required
def private_chat(request, user_id=None):
    # If no user_id is passed, show the list of all users
    if user_id is None:
        # Filter out the current user
        users = User.objects.exclude(id=request.user.id)
        return render(request, 'crm/private_chat_list.html', {'users': users})

    # Get the user to chat with
    user_to_chat = get_object_or_404(User, pk=user_id)
    
    # If the logged-in user is an agent, they can chat with anyone
    if not request.user.groups.filter(name='supervisor').exists():
        # Agents can chat with anyone, no permission check needed
        pass

    # Ensure there is only one PrivateChat instance for the pair
    # Get or create the chat between the two users (whether agent or supervisor)
    chat = PrivateChat.objects.filter(
        (Q(user1=request.user) & Q(user2=user_to_chat)) | 
        (Q(user1=user_to_chat) & Q(user2=request.user))
    ).first()
    
    # For supervisors, fetch all messages exchanged between this user and all other agents/supervisors
    if request.user.groups.filter(name='supervisor').exists():
        # Supervisors can see all messages between the two users
        messages = PrivateMessage.objects.filter(chat=chat).order_by('-timestamp')
    else:
        # For agents, show both sent and received messages (messages where the agent is either the sender or the receiver)
        messages = PrivateMessage.objects.filter(
            chat=chat,
            sender__in=[request.user, user_to_chat]  # Include messages sent by either user
        ).order_by('-timestamp')
        print(messages)

    # Handle sending messages
    if request.method == 'POST':
        message_content = request.POST.get('message')
        if message_content:
            PrivateMessage.objects.create(
                chat=chat, sender=request.user, content=message_content
            )
            return redirect('private_chat', user_id=user_to_chat.id)

    # Mark all unread messages as read (optional step for marking messages as read)
    PrivateMessage.objects.filter(
        chat=chat, 
        read=False, 
        sender__in=[request.user, user_to_chat]
    ).update(read=True)

    return render(request, 'crm/private_chat.html', {
        'chat': chat,
        'messages': messages,
        'user_to_chat': user_to_chat
    })

@login_required
def check_for_messages(request):
    # Get all unread messages for the current user
    unread_messages_count = PrivateMessage.objects.filter(
        read=False,
        chat__user1=request.user
    ).count() + PrivateMessage.objects.filter(
        read=False,
        chat__user2=request.user
    ).count()

    # Return the count of unread messages
    return JsonResponse({'unread_messages': unread_messages_count})