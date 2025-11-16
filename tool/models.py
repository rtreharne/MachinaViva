from django.db import models

class Assignment(models.Model):
    slug = models.SlugField(unique=True)  # matches Canvas resource_link_id
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    allow_multiple_submissions = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    user_id = models.CharField(max_length=255)  # From LTI claim: sub
    created_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to="submissions/")
    comment = models.TextField(blank=True)

    # Optional: store grade if using AGS later
    grade = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.user_id} → {self.assignment.title}"
