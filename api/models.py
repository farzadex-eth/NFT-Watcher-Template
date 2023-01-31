from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
import datetime


class Collection(models.Model):
    slug = models.CharField(max_length=512, unique=True, null=False)
    title = models.CharField(max_length=512)
    address = models.CharField(max_length=68)
    floor = models.FloatField()
    last_floor = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField()

    def num_watched(self):
        watchers = Watching.objects.filter(slug=self)
        return len(watchers)

    def num_active_targets(self):
        watchers = Watching.objects.filter(slug=self, active=True)
        return len(watchers)
        
    def num_watched_unique(self):
        watchers = Watching.objects.distinct('user_id').filter(slug=self)
        return len(watchers)

    def last_update(self):
        diff = timezone.now() - self.updated_at
        return str(int(diff.total_seconds() / 60)) + " minute(s) ago"

    def change(self):
        return (self.floor - self.last_floor)



class Watching(models.Model):
    slug = models.ForeignKey(Collection, on_delete=models.CASCADE)
    user_id = models.CharField(max_length=128)
    target_types = (
        (0, "value"),
        (1, "percentage")
    )
    target_type = models.IntegerField(choices=target_types, default=0)
    target = models.FloatField(validators=[MinValueValidator(0.0001)])
    current = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)


    
