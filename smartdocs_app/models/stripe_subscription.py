from django.db import models
from .user import CustomUser
from datetime import datetime, timezone

class stripe_subscription(models.Model):
    ACCESS_LEVEL_CHOICES =  [
        ('no-subscription', 'No Subscription'),
        ('level-0', 'Level 0'),
        ('level-1', 'Level 1'),
        ('level-2', 'Level 2'),
        ('level-3', 'Level 3')
    ]

    product_id = models.CharField(max_length=255)
    expiry_date = models.DateTimeField()
    user = models.ForeignKey(CustomUser, null=True, on_delete=models.SET_NULL)
    access_level = models.CharField(max_length=256, choices=ACCESS_LEVEL_CHOICES, default='no-subscription')
    is_active = models.BooleanField(default=True)
    update_date = models.DateTimeField(blank=True, null=True) 

    def __str__(self) -> str:
        return self.product_id
    

    def save(self, *args, **kwargs):
        if isinstance(self.expiry_date, (int, float)):
            self.expiry_date = datetime.fromtimestamp(self.expiry_date, tz=timezone.utc)
        super(stripe_subscription, self).save(*args, **kwargs)

    def get_remaining_time(self):
        current_time = datetime.now()
        remaining_time = self.expiry_date - current_time
        return remaining_time
    
    def get_remaining_time(self):
        current_time = datetime.now(timezone.utc)
        if self.expiry_date.tzinfo is None:
            self.expiry_date = self.expiry_date.replace(tzinfo=timezone.utc)
        remaining_time = self.expiry_date - current_time
        return remaining_time

    def is_expired(self):
        remaining_time = self.get_remaining_time()
        return remaining_time.total_seconds() <= 0