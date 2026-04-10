from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from accounts.models import CustomUser
from groups.models import ChatGroup
from chat.models import PrivateMessage, PrivateChat
from django.db.models import Q
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import urllib, base64
import pandas as pd
from django.utils import timezone
from datetime import timedelta

def generate_chart():
    days = []
    counts = []
    for i in range(6, -1, -1):
        date = timezone.now().date() - timedelta(days=i)
        count = PrivateMessage.objects.filter(created_at__date=date).count()
        days.append(date.strftime('%b %d'))
        counts.append(count)

    plt.figure(figsize=(8, 4))
    plt.plot(days, counts, marker='o', linestyle='-', color='#0d6efd')
    plt.title('Messages Sent Per Day')
    plt.xlabel('Date')
    plt.ylabel('Count')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    string = base64.b64encode(buf.read())
    uri = urllib.parse.quote(string)
    plt.close()
    return uri

@login_required
def user_dashboard(request):
    active_chats_count = PrivateChat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).count()
    groups_joined = request.user.chat_groups.count()
    total_messages_sent = PrivateMessage.objects.filter(sender=request.user).count()
    
    # Calculate unread
    unread_messages = PrivateMessage.objects.filter(
        chat__in=PrivateChat.objects.filter(Q(user1=request.user) | Q(user2=request.user)),
        is_read=False
    ).exclude(sender=request.user).count()
    
    chart_uri = generate_chart()
    
    context = {
        'active_chats_count': active_chats_count,
        'groups_joined': groups_joined,
        'total_messages_sent': total_messages_sent,
        'unread_messages': unread_messages,
        'chart_uri': chart_uri
    }
    return render(request, 'dashboard/user_dashboard.html', context)

@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('dashboard')
        
    total_users = CustomUser.objects.count()
    active_users = CustomUser.objects.filter(is_online=True).count()
    total_chats = PrivateChat.objects.count()
    total_groups = ChatGroup.objects.count()
    total_messages = PrivateMessage.objects.count()
    
    chart_uri = generate_chart()
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'total_chats': total_chats,
        'total_groups': total_groups,
        'total_messages': total_messages,
        'chart_uri': chart_uri
    }
    return render(request, 'dashboard/admin_dashboard.html', context)
