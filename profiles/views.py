from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from accounts.models import CustomUser
from .models import BlockedUser
from .forms import ProfileUpdateForm

@login_required
def search_users(request):
    query = request.GET.get('q')
    if query:
        users = CustomUser.objects.filter(
            Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)
        ).exclude(id=request.user.id)
    else:
        users = CustomUser.objects.none()
    return render(request, 'profiles/search_users.html', {'users': users, 'query': query})

@login_required
def profile_view(request, username):
    profile_user = get_object_or_404(CustomUser, username=username)
    is_blocked = BlockedUser.objects.filter(user=request.user, blocked_user=profile_user).exists()
    
    context = {
        'profile_user': profile_user,
        'is_blocked': is_blocked,
    }
    return render(request, 'profiles/profile_view.html', context)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            updated = form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile_view', username=updated.username)
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'profiles/edit_profile.html', {'form': form})

@login_required
def block_user(request, user_id):
    target_user = get_object_or_404(CustomUser, id=user_id)
    BlockedUser.objects.get_or_create(user=request.user, blocked_user=target_user)
    messages.success(request, f"You have blocked {target_user.username}.")
    return redirect('profile_view', username=target_user.username)
