from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ChatGroup, GroupMessage


@login_required
def group_list(request):
    my_groups = request.user.chat_groups.all().order_by('-created_at')
    discover_groups = ChatGroup.objects.filter(is_private=False).exclude(members=request.user).order_by('-created_at')
    return render(request, 'groups/group_list.html', {
        'my_groups': my_groups,
        'discover_groups': discover_groups,
    })


@login_required
def create_group(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        image = request.FILES.get('image')
        is_private = request.POST.get('is_private') == 'on'

        if not name:
            messages.error(request, "Group name is required.")
            return render(request, 'groups/create_group.html')

        group = ChatGroup(
            name=name,
            description=description,
            admin=request.user,
            is_private=is_private,
        )
        if image:
            group.image = image
        group.save()
        group.members.add(request.user)

        if is_private:
            messages.success(request, f"Private group '{name}' created! Share the code: {group.access_code}")
        else:
            messages.success(request, f"Group '{name}' created successfully!")
        return redirect('group_chat', group_id=group.id)

    return render(request, 'groups/create_group.html')


@login_required
def group_chat(request, group_id):
    group = get_object_or_404(ChatGroup, id=group_id)

    if request.user not in group.members.all():
        if group.is_private:
            messages.error(request, "This is a private group. You need an access code to join.")
            return redirect('group_list')
        else:
            group.members.add(request.user)
            messages.success(request, f"You joined {group.name}!")

    messages_history = group.messages.all().order_by('created_at')

    return render(request, 'groups/group_chat.html', {
        'group': group,
        'chat_messages': messages_history,
    })


@login_required
def join_private_group(request):
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        try:
            group = ChatGroup.objects.get(access_code=code)
            if request.user in group.members.all():
                messages.info(request, f"You are already a member of '{group.name}'.")
            else:
                group.members.add(request.user)
                messages.success(request, f"You joined '{group.name}'!")
            return redirect('group_chat', group_id=group.id)
        except ChatGroup.DoesNotExist:
            messages.error(request, "Invalid access code. Please check and try again.")
    return redirect('group_list')


@login_required
def leave_group(request, group_id):
    group = get_object_or_404(ChatGroup, id=group_id)
    if request.user in group.members.all():
        if group.admin == request.user:
            messages.error(request, "You are the admin. You cannot leave your own group.")
        else:
            group.members.remove(request.user)
            messages.success(request, f"You left '{group.name}'.")
    return redirect('group_list')
