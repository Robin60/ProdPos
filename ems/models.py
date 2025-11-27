from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


def generate_event_id():
    return f"EV-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:3].upper()}"
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

class Event(models.Model):
    PROJECT_TYPES = [
        ('kwp2', 'PROTECT WP2'),
        ('kwp3', 'PROTECT WP3'),
        ('kwp', 'PROTECT WP4'),
        ('other', 'Other'),
    ]

    event_id = models.CharField(
        max_length=20,
        unique=True,
        default=generate_event_id,
        editable=False,
        help_text="e.g., EV-20251109-1A2"
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    project_type = models.CharField(max_length=50, choices=PROJECT_TYPES)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    description = models.TextField(default='')
    location = models.CharField(max_length=255, default='')
    organizer = models.CharField(max_length=100, default='')
    participants = models.TextField(blank=True, null=True, help_text="Comma-separated list of participants")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
            return f"{self.name} ({self.user.username})"

class Outcome(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='outcome_entries')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    duration = models.FloatField(help_text="Duration in hours")
    rappo = models.CharField(max_length=150)
    topics = models.TextField()
    outcome_text = models.TextField()
    recommendation = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"Outcome for {self.event.name} ({self.start_date.date()})"
