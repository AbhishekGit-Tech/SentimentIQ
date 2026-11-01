from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Upload, Feedback, AspectResult


@admin.register(Upload)
class UploadAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "source", "created_at")


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("short_text", "overall_sentiment", "upload", "feedback_date")
    list_filter = ("overall_sentiment",)

    def short_text(self, obj):
        return obj.text[:60]


@admin.register(AspectResult)
class AspectResultAdmin(admin.ModelAdmin):
    list_display = ("aspect", "sentiment", "confidence", "feedback")
    list_filter = ("aspect", "sentiment")