from django.db import models
from django.conf import settings

# In a WhatsApp-like system, we don't necessarily have "Friend Requests".
# Anyone can start a conversation with anyone else (discovery by username/phone).
# We keep BlockedUser to allow users to stop unwanted messages.

class BlockedUser(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='blocking', on_delete=models.CASCADE)
    blocked_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='blocked_by', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'blocked_user')

    def __str__(self):
        return f"{self.user.username} blocked {self.blocked_user.username}"
