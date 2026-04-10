from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Notification

@receiver(post_save, sender=Notification)
def send_notification_realtime(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"notify_{instance.user.id}",
            {
                "type": "send_notification",
                "data": {
                    "message": instance.message,
                    "type": instance.notification_type,
                }
            }
        )
