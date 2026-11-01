from django.db import models

# Create your models here.
from django.conf import settings
from django.db import models
from django.utils import timezone


class Upload(models.Model):
    SOURCE_CHOICES = [("manual", "Manual entry"), ("csv", "CSV upload")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="uploads")
    name = models.CharField(max_length=200)
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.user})"


class Feedback(models.Model):
    upload = models.ForeignKey(Upload, on_delete=models.CASCADE, related_name="feedbacks")
    text = models.TextField()
    feedback_date = models.DateTimeField(default=timezone.now)   # trends isi se banenge
    overall_sentiment = models.CharField(max_length=10, blank=True)
    confidence = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.text[:50]


class AspectResult(models.Model):
    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE, related_name="aspect_results")
    segment_text = models.TextField()
    aspect = models.CharField(max_length=50)
    sentiment = models.CharField(max_length=10)
    confidence = models.FloatField()

    class Meta:
        indexes = [models.Index(fields=["aspect", "sentiment"])]

    def __str__(self):
        return f"{self.aspect}: {self.sentiment}"