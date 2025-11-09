from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from home import home_global_views

urlpatterns = [
    path("create_imprest/", views.create_imprest, name="create_imprest"),
    path("view_imprests/", views.view_imprests, name="view_imprests"),
    path('confirm_imprest/<int:imprest_id>/', views.confirm_imprest_payment, name='confirm_imprest'),
    path('fee_collection/', views.fee_collection, name='fee_collection'),
    path('get_trainee_info/', home_global_views.get_trainee_info, name='get_trainee_info'),
    path('collect_fee/', views.collect_fee, name='collect_fee'),
    path('all_payments/', views.all_payments, name='all_payments'),
    path('receipt/<str:payment_id>/', views.generate_receipt, name='generate_receipt'),
    path("fee-statements/", views.fee_statement_list, name="fee_statement_list"),
    path("fee-statements/<int:trainee_id>/pdf/", views.fee_statement, name="trainee_fee_statement_pdf"),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
