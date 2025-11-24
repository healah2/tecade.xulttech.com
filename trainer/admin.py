from django.contrib import admin
from .models import LearningGuide, SavedSessionPlan

@admin.register(LearningGuide)
class LearningGuideAdmin(admin.ModelAdmin):
    list_display = ('unit_competence', 'course', 'class_name', 'level')
    search_fields = ('unit_competence', 'course', 'class_name', 'level')

@admin.register(SavedSessionPlan)
class SavedSessionPlanAdmin(admin.ModelAdmin):
    list_display = (
        'session_title',
        'unit',
        'presenter_name',
        'date',
        'duration',
        'created_at',
    )
    list_filter = ('unit', 'date', 'created_at')
    search_fields = ('session_title', 'presenter_name', 'unit__unit_competence')
