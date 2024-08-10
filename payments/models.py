from django.db import models
from django.conf import settings
from django.utils import timezone


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subscription_active = models.BooleanField(default=False)
    resume_count = models.IntegerField(default=0)
    cover_letter_count = models.IntegerField(default=0)
    last_reset_date = models.DateField(default=timezone.now)  # Track when the count was last reset
    subscribed_plan = models.CharField(max_length=50, null=True, blank=True)  # Store the plan code or name
    subscription_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    subscription_start_date = models.DateField(null=True, blank=True)
    subscription_expiry_date = models.DateField(null=True, blank=True)

