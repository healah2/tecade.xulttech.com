from django.contrib import admin
from .models import LearningGuide

@admin.register(LearningGuide)
class LearningGuideAdmin(admin.ModelAdmin):
    list_display = ('course_name', 'level', 'start_date', 'end_date')
    search_fields = ('course_name', 'level')
