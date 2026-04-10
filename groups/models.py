import random
import string
from django.db import models
from django.conf import settings


def generate_access_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


class ChatGroup(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='group_pics/', default='group_pics/default_group.png', blank=True)
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='administered_groups')
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='chat_groups')
    is_private = models.BooleanField(default=False)
    access_code = models.CharField(max_length=8, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.access_code:
            code = generate_access_code()
            while ChatGroup.objects.filter(access_code=code).exists():
                code = generate_access_code()
            self.access_code = code
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class GroupMessage(models.Model):
    group = models.ForeignKey(ChatGroup, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField(blank=True)
    file = models.FileField(upload_to='group_files/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username} in {self.group.name}: {self.message[:20]}"
