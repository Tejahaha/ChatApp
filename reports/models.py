from django.db import models
from django.conf import settings

class Report(models.Model):
    REASON_CHOICES = (
        ('spam', 'Spam'),
        ('harassment', 'Harassment'),
        ('inappropriate', 'Inappropriate Content'),
        ('other', 'Other'),
    )
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='reports_made', on_delete=models.CASCADE)
    reported_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='reports_received', on_delete=models.CASCADE)
    message = models.TextField(blank=True, help_text="Reference the message if applicable")
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report against {self.reported_user.username} by {self.reported_by.username}"
