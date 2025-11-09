from django.utils import timezone
import random, string
from django.db import models
from django.utils import timezone


class Imprest(models.Model):
    imprest_number = models.CharField(max_length=20, unique=True, editable=False)
    name_of_holder = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    amount_generated = models.DecimalField(max_digits=12, decimal_places=2)
    date_generated = models.DateField(default=timezone.now)

    # New fields
    STATUS_CHOICES = [
        ("Unpaid", "Unpaid"),
        ("Paid", "Paid"),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Unpaid")
    date_confirmed = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.imprest_number:
            rand_num = random.randint(100, 999)
            rand_letters = ''.join(random.choices(string.ascii_uppercase, k=4))
            today = timezone.now()
            month_initial = today.strftime("%b")[0].upper()   # e.g. A for Aug
            date_part = today.strftime("%d") + month_initial  # e.g. 16A
            self.imprest_number = f"IM{rand_num}{rand_letters}{date_part}"
        super().save(*args, **kwargs)

    def confirm_payment(self):
        """Call this method when confirming an imprest payment"""
        self.status = "Paid"
        self.date_confirmed = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.imprest_number} - {self.name_of_holder} ({self.status})"



# finance/models.py
from django.db import models
from django.utils import timezone

class FeePayment(models.Model):
    trainee = models.ForeignKey("home.Trainee", on_delete=models.CASCADE)
    trainee_session = models.ForeignKey("home.TraineeSession", on_delete=models.CASCADE)
    item_of_payment = models.CharField(max_length=255)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    mode_of_payment = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=255)
    date_paid = models.DateTimeField(auto_now_add=True)
    payment_id = models.CharField(max_length=10, unique=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.payment_id:
            self.payment_id = self.generate_payment_id()
        super().save(*args, **kwargs)

    def generate_payment_id(self):
        import random, string
        while True:
            digits = ''.join(random.choices(string.digits, k=5))
            letters = ''.join(random.choices(string.ascii_uppercase, k=5))
            payment_id = f"{digits}{letters}"
            if not FeePayment.objects.filter(payment_id=payment_id).exists():
                return payment_id

    def __str__(self):
        return f"{self.payment_id} - {self.trainee}"

from django.db import models
from django.utils import timezone

class FeeStatement(models.Model):
    trainee = models.ForeignKey("home.Trainee", on_delete=models.CASCADE)
    
    TRANSACTION_CHOICES = (
        ("DEBIT", "Debit"),
        ("CREDIT", "Credit"),
    )

    YEAR_CHOICES = [
        ('1', 'First Year'),
        ('2', 'Second Year'),
        ('3', 'Third Year'),
    ]

    TERM_CHOICES = [
        ('1', 'Term 1'),
        ('2', 'Term 2'),
        ('3', 'Term 3'),
    ]

    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)
    invoice_number = models.CharField(max_length=50, blank=True, null=True)
    reference = models.CharField(max_length=50, blank=True, null=True)
    session_period = models.CharField(max_length=20)

    year_of_study = models.CharField(max_length=1, choices=YEAR_CHOICES)
    term = models.CharField(max_length=1, choices=TERM_CHOICES)

    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.trainee} - {self.session_period} - {self.transaction_type}"


