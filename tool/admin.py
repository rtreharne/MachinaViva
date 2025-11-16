from django.contrib import admin
from .models import Assignment, Submission

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "allow_multiple_submissions")
    search_fields = ("title", "slug")

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("assignment", "user_id", "created_at", "grade")
    search_fields = ("user_id",)
    list_filter = ("assignment",)
