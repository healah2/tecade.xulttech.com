from django.urls import path
from . import views

urlpatterns = [
    path("generate_learning_plan/", views.generate_learning_plan, name="generate_learning_plan"),
    path("learning_guides_list/", views.learning_guides_list, name="learning_guides_list"),
    path("view_learning_guide/<int:pk>/", views.view_learning_guide, name="view_learning_guide"),
]
