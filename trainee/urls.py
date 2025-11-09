# # trainee/urls.py
# from django.urls import path
# from . import views

# app_name = "trainee"

# urlpatterns = [
#     path('trainee_dashboard/', views.trainee_dashboard, name='trainee_dashboard'),
#     path('attendance/', views.attendance, name='attendance'),
#     path('assignment/', views.assignment, name='assignment'),
#     # path('timetable/', views.timetable, name='timetable'),

#     path('profile/<int:trainee_number>/', views.traine_profile, name='profile'),
#     path('trainee_change_password/', views.trainee_change_password, name='trainee_change_password'),
#     path('trainee_login/', views.trainee_login, name='trainee_login'),
#     path('logout/', views.trainee_logout, name='logout'),

#     # Timetable management
#     path('manage-timetable/', views.manage_timetable, name='manage_timetable'),
#     path('edit-timetable/<int:timetable_id>/', views.edit_timetable, name='edit_timetable'),
#     path('delete-timetable/<int:timetable_id>/', views.delete_timetable, name='delete_timetable'),
#     path('manage-sessions/<int:timetable_id>/', views.manage_sessions, name='manage_sessions'),
#     path('edit-session/<int:session_id>/', views.edit_session, name='edit_session'),
#     path('delete-session/<int:session_id>/', views.delete_session, name='delete_session'),
#     path('trainee_timetable/', views.timetable_view, name='trainee_timetable'),

#     # ====================Detailed BLOG carousel==================================
#     path('notice/<int:pk>/', views.notice_detail, name='notice_detail'),  
#     path('upload-notice/', views.upload_notice, name='upload_notice'),  
#     # path('ws/home/', views.ws_home, name='ws_home'),
    
#     path('attendance/', views.attendance, name='attendance'),
#     path('library/', views.library, name='library'),
#     path('assignment/', views.assignment, name='assignment'),
#     # path('timetable/', views.timetable, name='timetable'),
#         # To handle the trainee profile page different from trainees urls
#     path('traine_profile/<int:trainee_id>/', views.traine_profile, name='traine_profile'),
#     path('trainee/change-password/', views.trainee_change_password, name='trainee_change_password'),
#     # path('login/', views.trainee_login, name='trainee_login'),  # Your existing login URL
#     path('trainee/logout/', views.trainee_logout, name='trainee_logout'),
#     path('trainee/change-password/', views.trainee_change_password, name='trainee_change_password'),
# ]


# trainee/urls.py
from django.urls import path
from . import views

app_name = "trainee"

urlpatterns = [
    path('trainee_dashboard/', views.trainee_dashboard, name='trainee_dashboard'),
    path('attendance/', views.attendance, name='attendance'),
    # path('assignment/', views.assignment, name='assignment'),
    # path('timetable/', views.timetable, name='timetable'),

    path('profile/<int:trainee_number>/', views.traine_profile, name='profile'),
    path('trainee_change_password/', views.trainee_change_password, name='trainee_change_password'),
    path('trainee_login/', views.trainee_login, name='trainee_login'),
    path('logout/', views.trainee_logout, name='logout'),

    # Timetable management
    path('manage-timetable/', views.manage_timetable, name='manage_timetable'),
    path('edit-timetable/<int:timetable_id>/', views.edit_timetable, name='edit_timetable'),
    path('delete-timetable/<int:timetable_id>/', views.delete_timetable, name='delete_timetable'),
    path('manage-sessions/<int:timetable_id>/', views.manage_sessions, name='manage_sessions'),
    path('edit-session/<int:session_id>/', views.edit_session, name='edit_session'),
    path('delete-session/<int:session_id>/', views.delete_session, name='delete_session'),
    path('trainee_timetable/', views.timetable_view, name='trainee_timetable'),

    # ====================Detailed BLOG carousel==================================
    path('notice/<int:pk>/', views.notice_detail, name='notice_detail'),  
    path('upload-notice/', views.upload_notice, name='upload_notice'),  
    # path('ws/home/', views.ws_home, name='ws_home'),
    
    path('attendance/', views.attendance, name='attendance'),
    # path('library/', views.library, name='library'),
    path('tecade_bot/', views.tecade_bot, name='tecade_bot'),
    path('library/<int:trainee_id>/', views.library, name='library_detail'),
    path('love_book/<str:google_id>/', views.love_book, name='love_book'),
    # path('assignment/<int:trainee_id>/', views.assignment, name='assignment'),
    # path('timetable/', views.timetable, name='timetable'),
        # To handle the trainee profile page different from trainees urls
    path('traine_profile/<int:trainee_id>/', views.traine_profile, name='traine_profile'),
    path('trainee/change-password/', views.trainee_change_password, name='trainee_change_password'),
    path('login/', views.trainee_login, name='trainee_login'),  # Your existing login URL
    path('trainee/logout/', views.trainee_logout, name='trainee_logout'),
    path('trainee/change-password/', views.trainee_change_password, name='trainee_change_password'),

# ---------------------------------------

# ASSIGNMENTS URLS
# ---------------------------------------

    path('assignment/<int:trainee_id>/', views.assignment_list, name='assignment_list'),
    path('submit/<int:assignment_id>/', views.submit_assignment, name='submit_assignment'),

    path('assignments/', views.admin_assignments, name='admin_assignments'),
    path('assignments/create/', views.create_assignment, name='create_assignment'),
    path('assignments/<int:assignment_id>/submissions/', views.view_submissions, name='view_submissions'),
    path('submissions/<int:submission_id>/grade/', views.grade_submission, name='grade_submission'),

# -------------------------------------------------

# ATTENDANCE URLS

# -------------------------------------------------
    path('create_register/', views.create_register, name='create_register'),
    path('mark_attendance/<int:register_id>/', views.mark_attendance, name='mark_attendance'),
    path('dashboard/', views.trainer_dashboard, name='trainer_dashboard'),
    path('excuse_request/<int:request_id>/', views.handle_excuse_request, name='handle_excuse_request'),
    
    # Trainee URLs
    path('attendance/', views.trainee_attendance, name='trainee_attendance'),
    path('submit_excuse/', views.submit_excuse_request, name='submit_excuse_request'),
    
    # API URLs for AJAX calls
    # path('api/attendance_stats/', views.attendance_stats_api, name='attendance_stats_api'),
    path('api/attendance/data/', views.trainee_attendance_data, name='trainee_attendance_data'),
    path('api/attendance/calendar/', views.trainee_attendance_calendar, name='trainee_attendance_calendar'),
    path('api/trainee/excuse-request/', views.handle_excuse_request, name='handle_excuse_request'),

    path('portfolio_dashboard/', views.portfolio_dashboard, name='portfolio_dashboard'),
    path('evidence/', views.portfolio_evidence, name='portfolio_evidence'),
    path('upload/', views.portfolio_upload, name='portfolio_upload'),
    path('reflections/', views.portfolio_reflections, name='portfolio_reflections'),
    path('edit_reflection/', views.edit_reflection, name='edit_reflection'),
    path('portfolio/reflections/edit/<int:reflection_id>/', views.edit_reflection, name='edit_reflection'),
    path('share/', views.portfolio_share, name='portfolio_share'),
    path('shared/<uuid:token>/', views.portfolio_shared, name='portfolio_shared'),

    #   urls for fee statement check 
    # path('dashboard/', views.trainee_dashboard, name='trainee_dashboard'),
    path('register-session/', views.trainee_register_session, name='register_session'),
    path('fee-statement/', views.trainee_fee_statement, name='fee_statement'),
    path('dashiboard/', views.portfolio_dashiboard, name='portfolio_dashiboard'),

]





