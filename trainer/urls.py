from django.urls import path
from . import views

urlpatterns = [
    path("generate_learning_plan/", views.generate_learning_plan, name="generate_learning_plan"),
    path("learning_guides_list/", views.learning_guides_list, name="learning_guides_list"),
    path("view_learning_guide/<int:pk>/", views.view_learning_guide, name="view_learning_guide"),
    path('session_plan/<int:session_no>/', views.session_plan, name='session_plan'),
    path('generate_session_plan/', views.generate_session_plan, name='generate_session_plan'),
    path('session_plans_list/', views.session_plans_list, name='session_plans_list'),
    path('view_session_plan/<int:plan_id>/', views.view_session_plan, name='view_session_plan'),
    path("sp/", views.sp, name='sp' )
]
