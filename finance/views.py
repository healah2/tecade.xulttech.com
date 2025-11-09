from django.shortcuts import render, redirect
import random
from decimal import Decimal
from itertools import groupby
from operator import attrgetter
from collections import defaultdict

from django.db.models import F, Max
from django.utils import timezone
from django.utils.timezone import now
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.template.loader import get_template
from django.contrib import messages

from home import home_global_views
from home.models import Trainee, TraineeSession, CurrentSession
from finance.models import FeePayment, FeeStatement, Imprest


def create_imprest(request):
    if request.method == 'POST':
        name = request.POST.get('name_of_holder')
        phone = request.POST.get('phone_number')
        email = request.POST.get('email')
        amount = request.POST.get('amount_generated')
        date_generated = request.POST.get('date_generated') or timezone.now().date()

        imprest = Imprest(
            name_of_holder=name,
            phone_number=phone,
            email=email,
            amount_generated=amount,
            date_generated=date_generated
        )
        imprest.save()
        return redirect('view_imprests')  # redirect to list page

    return render(request, 'finance/create_imprest.html')


def view_imprests(request):
    imprests = Imprest.objects.all().order_by('-date_generated')
    return render(request, 'finance/view_imprests.html', {'imprests': imprests})



def confirm_imprest_payment(request, imprest_id):
    imprest = get_object_or_404(Imprest, id=imprest_id)
    if imprest.status == "Unpaid":   # only confirm unpaid
        imprest.status = "Paid"
        imprest.date_confirmed = timezone.now()
        imprest.save()
        messages.success(request, f"Imprest {imprest.imprest_number} has been confirmed as Paid.")
    else:
        messages.warning(request, f"Imprest {imprest.imprest_number} is already marked as {imprest.status}.")
    return redirect("view_imprests")  # adjust to your actual view name

def fee_collection(request):
    return render(request, 'finance/fee_collection.html')

# finance/views.py (or home_global_views.py)


# finance/views.py


def collect_fee(request):
    if request.method == 'POST':
        trainee_number = request.POST.get('trainee_number', '').strip()
        item_of_payment = request.POST.get('item_of_payment')
        amount_paid = request.POST.get('amount_paid')
        mode_of_payment = request.POST.get('mode_of_payment')
        transaction_id = request.POST.get('transaction_id')

        if not all([trainee_number, item_of_payment, amount_paid, mode_of_payment, transaction_id]):
            messages.error(request, "All fields are required.")
            return redirect(request.META.get('HTTP_REFERER'))

        try:
            amount_paid = Decimal(amount_paid)
            if amount_paid <= 0:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, "Amount paid must be a valid positive number.")
            return redirect(request.META.get('HTTP_REFERER'))

        try:
            trainee = Trainee.objects.get(trainee_number=trainee_number)
        except Trainee.DoesNotExist:
            messages.error(request, "Trainee not found.")
            return redirect(request.META.get('HTTP_REFERER'))

        try:
            current_session = CurrentSession.objects.get(is_active=True)
        except CurrentSession.DoesNotExist:
            messages.error(request, "No active session found.")
            return redirect(request.META.get('HTTP_REFERER'))

        try:
            trainee_session = TraineeSession.objects.get(trainee=trainee, current_session=current_session)
        except TraineeSession.DoesNotExist:
            messages.error(request, "Trainee is not in the current active session.")
            return redirect(request.META.get('HTTP_REFERER'))

        # Save FeePayment
        payment = FeePayment.objects.create(
            trainee=trainee,
            trainee_session=trainee_session,
            item_of_payment=item_of_payment,
            amount_paid=amount_paid,
            mode_of_payment=mode_of_payment,
            transaction_id=transaction_id
        )

        # Update balance
        trainee_session.fee_balance -= amount_paid
        trainee_session.save(update_fields=['fee_balance'])

        # ✅ Create FeeStatement CREDIT entry (now with term and year)
        FeeStatement.objects.create(
            trainee=trainee,
            transaction_type="CREDIT",
            amount=amount_paid,
            balance_after=trainee_session.fee_balance,
            invoice_number=payment.payment_id,  # use real payment ID
            reference=payment.payment_id,
            session_period=trainee_session.session_period,
            year_of_study=trainee_session.year_of_study,   # ✅ add year
            term=trainee_session.term                       # ✅ add term
        )

        if trainee_session.fee_balance < 0:
            messages.success(
                request,
                f"Payment of KES {amount_paid} collected for {trainee}. Overpaid by KES {abs(trainee_session.fee_balance)}."
            )
        else:
            messages.success(
                request,
                f"Payment of KES {amount_paid} collected for {trainee}. Remaining balance: KES {trainee_session.fee_balance}."
            )

        return redirect(request.META.get('HTTP_REFERER'))

    return redirect('fee_collection')




# finance/views.py


def all_payments(request):
    payments = FeePayment.objects.select_related('trainee').all().order_by('-date_paid')
    
    context = {
        "payments": payments
    }
    return render(request, "finance/all_payments.html", context)

def generate_receipt(request, payment_id):
    payment = get_object_or_404(FeePayment, payment_id=payment_id)

    # Generate receipt number: TECADE/DD/MONTH/YYYY/Random5Digits
    today = now()
    random_digits = f"{random.randint(10000, 99999)}"
    receipt_number = f"TECADE/{today.day}/{today.strftime('%b').upper()}/{today.year}/{random_digits}"

    context = {
        "payment": payment,
        "receipt_number": receipt_number
    }
    return render(request, "finance/fees_receipt.html", context)





def fee_statement_list(request):
    # Get the latest statement per trainee
    latest_statements = (
        FeeStatement.objects
        .values("trainee")  # group by trainee
        .annotate(latest_date=Max("date"))  # latest date per trainee
    )

    # Join back to get trainee details + latest balance
    trainees = (
        FeeStatement.objects.filter(
            date__in=[entry["latest_date"] for entry in latest_statements],
            trainee_id__in=[entry["trainee"] for entry in latest_statements],
        )
        .values(
            "trainee__id",
            "trainee__trainee_number",
            "trainee__first_name",
            "trainee__last_name",
            "balance_after",
        )
    )

    return render(request, "finance/fee_statement_list.html", {"trainees": trainees})




def fee_statement(request, trainee_id):
    trainee = get_object_or_404(Trainee, id=trainee_id)

    # Order statements by date
    statements = FeeStatement.objects.filter(trainee=trainee).order_by("date")

    TERM_MAP = {'1': 'Term 1', '2': 'Term 2', '3': 'Term 3'}
    YEAR_MAP = {'1': 'First Year', '2': 'Second Year', '3': 'Third Year'}

    # Group by session with "termly balance" (from last transaction in that session)
    grouped_statements = defaultdict(lambda: {"items": [], "termly_balance": 0})

    for stmt in statements:
        term_label = TERM_MAP.get(str(stmt.term), stmt.term)
        year_label = YEAR_MAP.get(str(stmt.year_of_study), stmt.year_of_study)
        session_label = f"{year_label} - {term_label}"

        grouped_statements[session_label]["items"].append(stmt)

    # ✅ now fetch last balance_after for each session
    for session_label, data in grouped_statements.items():
        last_stmt = data["items"][-1]  # last item (because statements are ordered by date)
        grouped_statements[session_label]["termly_balance"] = last_stmt.balance_after

    # Get latest/current trainee session
    trainee_session = (
        TraineeSession.objects.filter(trainee=trainee)
        .order_by("-created_at")
        .first()
    )

    context = {
        "trainee": trainee,
        "trainee_session": trainee_session,
        "grouped_statements": grouped_statements.items(),
        "now": now(),
    }
    return render(request, "finance/fee_statement.html", context)





