from django.db import models

from django.db import models
import json

class LearningGuide(models.Model):
    unit_code = models.CharField(max_length=50, null=True, blank=True)
    unit_competence = models.TextField(null=True, blank=True)
    trainer_name = models.CharField(max_length=100, null=True, blank=True)
    course = models.CharField(max_length=100, null=True, blank=True)
    institution = models.CharField(max_length=100, null=True, blank=True)

    date_preparation = models.DateField(null=True, blank=True)
    date_revision = models.DateField(null=True, blank=True)

    term = models.CharField(max_length=50, null=True, blank=True)
    trainees = models.CharField(max_length=200, null=True, blank=True)  # comma-separated list
    class_name = models.CharField(max_length=50, null=True, blank=True)
    total_time = models.IntegerField(null=True, blank=True)  # in hours

    # Stores sessions as JSON string
    sessions_json = models.TextField(null=True, blank=True)

    level = models.CharField(max_length=50, null=True, blank=True)  # trainee level or program level

    date_created = models.DateTimeField(null=True, blank=True,)

    def __str__(self):
        return f"{self.unit_code} - {self.trainer_name}"

    @property
    def sessions(self):
        """
        Returns the session list as Python objects.
        Handles both JSONField style & raw text JSON safely.
        """
        if not self.sessions_json:
            return []
        try:
            return json.loads(self.sessions_json)
        except:
            return []

class SavedSessionPlan(models.Model):
    unit = models.ForeignKey('LearningGuide', on_delete=models.CASCADE)

    # Core info
    session_title = models.CharField(max_length=255)
    duration = models.PositiveIntegerField(null=True, blank=True)  # in minutes
    presenter_name = models.CharField(max_length=255)
    date = models.DateField()

    # Form fields
    bridge_in = models.CharField(max_length=50, blank=True)
    pre_assessment = models.CharField(max_length=50, blank=True)
    post_assessment = models.CharField(max_length=50, blank=True)
    summary = models.CharField(max_length=255, blank=True)
    time = models.TextField(blank=True)  # stored as newline text

    # Auto-populated / dynamic fields
    expectation = models.TextField(blank=True)
    trainer_activities = models.TextField(blank=True)   # stored as newline text
    trainee_activities = models.TextField(blank=True)   # stored as newline text
    resources = models.TextField(blank=True)            # stored as newline text

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.session_title} - {self.unit.unit_competence}"

