from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import PrivateChat, PrivateMessage
from accounts.models import CustomUser


@login_required
def chat_list(request):
    chats = PrivateChat.objects.filter(Q(user1=request.user) | Q(user2=request.user))

    chat_data = []
    for chat in chats:
        other_user = chat.user2 if chat.user1 == request.user else chat.user1
        last_message = chat.messages.order_by('-created_at').first()
        unread_count = chat.messages.filter(sender=other_user, is_read=False).count()
        chat_data.append({
            'chat': chat,
            'other_user': other_user,
            'last_message': last_message,
            'unread_count': unread_count,
        })

    # Sort by last message time descending
    chat_data.sort(
        key=lambda x: x['last_message'].created_at if x['last_message'] else x['chat'].created_at,
        reverse=True,
    )

    return render(request, 'chat/chat_list.html', {'chats': chat_data})


@login_required
def private_chat(request, user_id):
    other_user = get_object_or_404(CustomUser, id=user_id)
    if other_user == request.user:
        return redirect('chat_list')

    chat = PrivateChat.objects.filter(
        (Q(user1=request.user) & Q(user2=other_user)) |
        (Q(user1=other_user) & Q(user2=request.user))
    ).first()

    if not chat:
        chat = PrivateChat.objects.create(user1=request.user, user2=other_user)

    # Mark incoming messages as read
    chat.messages.filter(sender=other_user, is_read=False).update(is_read=True)

    messages = chat.messages.all().order_by('created_at')

    users = sorted([request.user.username, other_user.username])
    room_name = f"{users[0]}_{users[1]}"

    context = {
        'chat': chat,
        'other_user': other_user,
        'chat_messages': messages,
        'room_name': room_name,
    }
    return render(request, 'chat/private_chat.html', context)
