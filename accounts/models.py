from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class CustomUser(AbstractUser):
    profile_image = models.ImageField(upload_to='profile_pics/', default='profile_pics/default.png', blank=True)
    bio = models.TextField(max_length=500, blank=True)
    status_message = models.CharField(max_length=255, blank=True)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.username
