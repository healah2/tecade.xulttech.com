from django.db import models

class LearningGuide(models.Model):
    course_name = models.CharField(max_length=255)
    level = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    document = models.FileField(upload_to="learning_guides/")
    html_content = models.TextField(blank=True, null=True)  # converted docx → HTML
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.course_name} (Level {self.level}) [{self.start_date} → {self.end_date}]"

