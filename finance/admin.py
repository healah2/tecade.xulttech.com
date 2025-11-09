
from django.contrib import admin
from .models import Imprest
from .models import FeePayment, FeeStatement

@admin.register(Imprest)
class ImprestAdmin(admin.ModelAdmin):
    list_display = ('imprest_number', 'name_of_holder', 'phone_number', 'email', 'amount_generated', 'date_generated')
    search_fields = ('imprest_number', 'name_of_holder', 'email', 'phone_number')
    list_filter = ('date_generated', )
    ordering = ('-date_generated',)


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ('trainee', 'item_of_payment', 'amount_paid', 'mode_of_payment', 'transaction_id', 'date_paid', 'payment_id')
    search_fields = ('trainee__name', 'item_of_payment', 'transaction_id', 'payment_id')
    list_filter = ('date_paid', 'mode_of_payment')

@admin.register(FeeStatement)
class FeeStatementAdmin(admin.ModelAdmin):
    list_display = ('trainee', 'transaction_type', 'amount', 'balance_after',
                    'session_period', 'year_of_study', 'term', 'date')
    list_filter = ('transaction_type', 'session_period', 'year_of_study', 'term', 'date')
    search_fields = ('trainee__trainee_number', 'invoice_number', 'reference')