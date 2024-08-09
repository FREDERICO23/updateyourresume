from django.db import models
from django.conf import settings
from django.utils import timezone


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subscription_active = models.BooleanField(default=False)
    resume_count = models.IntegerField(default=0)
    cover_letter_count = models.IntegerField(default=0)
    last_reset_date = models.DateField(default=timezone.now)  # Track when the count was last reset

