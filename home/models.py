from django.db import models
from django.core.validators import FileExtensionValidator
from django.conf import settings
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone

User = get_user_model()

class AdminIndex(models.Model):
    # Facts Section
    num_institutions = models.PositiveIntegerField(default=0)
    num_trainees = models.PositiveIntegerField(default=0)
    num_trainers = models.PositiveIntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Admin Index Content"

    
class CarouselSlide(models.Model):
    admin_index = models.ForeignKey(AdminIndex, on_delete=models.CASCADE, related_name='slides')
    image = models.ImageField(upload_to='carousel/')
    heading = models.CharField(max_length=255)
    subheading = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0, help_text="Controls the order of slides")

    def __str__(self):
        return self.heading
    




class AdminAbout(models.Model):
    title = models.CharField(max_length=255, default="Empowering Institutions & Learners Across Kenya")
    paragraph1 = models.TextField()
    paragraph2 = models.TextField()
    paragraph3 = models.TextField()
    phone = models.CharField(max_length=50, default="+012 345 6789")
    image = models.ImageField(upload_to='about_images/', blank=True, null=True)

    def __str__(self):
        return self.title


class AdminInstitutionalManagement(models.Model):
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='team/')
    twitter = models.URLField(blank=True, null=True)
    facebook = models.URLField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name
    
class AdminBom(models.Model):
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='team/')
    twitter = models.URLField(blank=True, null=True)
    facebook = models.URLField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name
    
class AdminAcDpt(models.Model):
    name = models.CharField(max_length=100)  # Department name
    image = models.ImageField(upload_to='departments/')
    heading = models.CharField(max_length=255)  # Section heading
    description = models.TextField()
    read_more_link = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name
    
class AdminNonAcDpt(models.Model):
    name = models.CharField(max_length=100)  # Department name
    image = models.ImageField(upload_to='departments/')
    heading = models.CharField(max_length=255)  # Section heading
    description = models.TextField()
    read_more_link = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name
    
# models.py
from django.utils import timezone

class Department(models.Model):
    name = models.CharField(max_length=100)
    date_registered = models.DateField(auto_now_add=True)
    code = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name



class Course(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    level = models.CharField(max_length=50)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    date_registered = models.DateField()

    term1_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    term2_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    term3_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_fees = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0)

    def save(self, *args, **kwargs):
        self.total_fees = self.term1_fees + self.term2_fees + self.term3_fees
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

from django.db import models
import re

from django.db import models
from django.core.validators import FileExtensionValidator
from django.contrib.auth.hashers import make_password, check_password


class Trainee(models.Model):
    
    #+++++++++++++++ Field to authenticate the trainee+++++++++++++++++
    password = models.CharField(max_length=128, blank=True, default='')  # Stores hashed password
    last_login = models.DateTimeField(null=True, blank=True)  # Track last login
    # ++++++++++++++++++++++ENDS HERE+++++++++++++++++++++++++++++++++++++ 
    
    # Personal Info
    passport_image = models.ImageField(
        upload_to='trainee_passports/',
        default='img/default.jpg',  # assuming it's in STATICFILES_DIRS
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(
        max_length=10,
        choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')],
        null=True,
        blank=True
    )

    age = models.PositiveIntegerField()
    date_of_admission = models.DateField()

    # Course Info
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True)
    course = models.ForeignKey('Course', on_delete=models.SET_NULL, null=True)
    
    # Auto-generated trainee number
    trainee_number = models.CharField(max_length=50, blank=True, editable=False, unique=True)

    # Academic Background
    kcse_index = models.CharField(max_length=50, blank=True, null=True)
    kcse_grade = models.CharField(max_length=5, blank=True, null=True)
    kcse_year = models.IntegerField(blank=True, null=True)
    kcpe_index = models.CharField(max_length=50, blank=True, null=True)
    kcpe_grade = models.CharField(max_length=5, blank=True, null=True)
    kcpe_year = models.IntegerField(blank=True, null=True)

    # Residential Info
    county = models.CharField(max_length=100, blank=True, null=True)
    sub_county = models.CharField(max_length=100, blank=True, null=True)
    division = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)

    # Contact Info
    phone = models.CharField(max_length=20)
    id_number = models.CharField(max_length=20)
    email = models.EmailField()

    # Guardian Info
    guardian_name = models.CharField(max_length=100)
    guardian_phone = models.CharField(max_length=20)
    guardian_id = models.CharField(max_length=20)

    def generate_trainee_number(self, number_part_override=None):
        import re

        # 1. Extract level code (e.g. "L6") from course name
        level_match = re.match(r"(L\d+)", self.course.name)
        level_code = level_match.group(1) if level_match else "L?"

        # 2. Extract abbreviation from course name: (CS)
        course_match = re.search(r'\((.*?)\)', self.course.name)
        course_abbr = course_match.group(1) if course_match else self.course.name[:2].upper()

        # 3. Intake code: e.g., 2025-07-01 → 25J
        year_suffix = self.date_of_admission.strftime("%y")
        month_abbr = self.date_of_admission.strftime("%B")[:1].upper()
        intake_code = f"{year_suffix}{month_abbr}"

        # 4. Use override or generate new sequence number
        if number_part_override:
            number_part = number_part_override
        else:
            count = Trainee.objects.count() + 1
            number_part = f"{count:04d}"

        # 5. Final format
        return f"{level_code}/{course_abbr}/{number_part}/{intake_code}"

    def regenerate_trainee_number(self):
        self.trainee_number = self.generate_trainee_number()
        self.save(update_fields=['trainee_number'])

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def save(self, *args, **kwargs):
        # 1. Generate trainee number if not already set
        if not self.trainee_number and self.course and self.date_of_admission:
            self.trainee_number = self.generate_trainee_number()

        # 2. Set initial password to trainee_number if password is empty
        if not self.password and self.trainee_number:
            self.set_password(self.trainee_number)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.trainee_number})"

    @property
    def is_authenticated(self):
        return True

    


from django.db import models

class AdminCredentials(models.Model):
    username = models.CharField(max_length=150, unique=True)
    name = models.CharField(max_length=200)
    designation = models.CharField(max_length=100)
    staff_number = models.CharField(max_length=50, unique=True)
    profile_image = models.ImageField(upload_to='admin_profiles/', blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.username})"

from django.core.exceptions import ValidationError

from django.db import models
from django.core.exceptions import ValidationError



from django.core.exceptions import ValidationError

from django.db import models
from django.core.exceptions import ValidationError



from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class CurrentSession(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    session_period = models.CharField(max_length=255, null=True, editable=False)

    def clean(self):
        if self.end_date <= self.start_date:
            raise ValidationError("End date must be after start date.")

    def save(self, *args, **kwargs):
        # Set session_period automatically
        self.session_period = f"{self.start_date} → {self.end_date}"

        # Auto-expire past sessions
        if self.end_date < timezone.now().date():
            self.is_active = False

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Session {self.session_period} - {'Active' if self.is_active else 'Expired'}"


class TraineeSession(models.Model):
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

    trainee = models.ForeignKey("Trainee", on_delete=models.CASCADE)
    current_session = models.ForeignKey("CurrentSession", on_delete=models.CASCADE, null=True, blank=True)
    year_of_study = models.CharField(max_length=1, choices=YEAR_CHOICES)
    term = models.CharField(max_length=1, choices=TERM_CHOICES)
    fee_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date_registered = models.DateField(auto_now_add=True)
    session_period = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def clean(self):
        """Keep your existing duplicate + sequential validation"""
        if TraineeSession.objects.filter(
            trainee=self.trainee,
            current_session=self.current_session
        ).exclude(id=self.id).exists():
            raise ValidationError("This trainee is already registered for the current session.")

    def save(self, *args, **kwargs):
        # Auto-assign Year/Term progression when creating
        if not self.id:
            last_session = TraineeSession.objects.filter(
                trainee=self.trainee
            ).order_by('year_of_study', 'term').last()

            if last_session:
                # progress from last term
                year = int(last_session.year_of_study)
                term = int(last_session.term) + 1
                if term > 3:
                    term = 1
                    year += 1
                self.year_of_study = str(year)
                self.term = str(term)
            else:
                # First ever session
                self.year_of_study = '1'
                self.term = '1'

            # Determine fee for this term
            term_fee = 0
            if self.term == '1':
                term_fee = self.trainee.course.term1_fees
            elif self.term == '2':
                term_fee = self.trainee.course.term2_fees
            elif self.term == '3':
                term_fee = self.trainee.course.term3_fees

            # Carry forward last balance
            carry_forward = last_session.fee_balance if last_session else 0
            self.fee_balance = term_fee + carry_forward

            # Copy current session period string
            if self.current_session:
                self.session_period = self.current_session.session_period

        super().save(*args, **kwargs)

    @property
    def overpaid_amount(self):
        """Return positive amount if there is overpayment (negative balance)."""
        return abs(self.fee_balance) if self.fee_balance < 0 else 0

    def __str__(self):
        return f"{self.trainee} - Year {self.year_of_study}, Term {self.term} ({self.session_period})"
        
# ===============Notice models=============
from django.urls import reverse
from django.utils.text import slugify

class Notice(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    # date_posted = models.DateTimeField(auto_now_add=False)
    memo_image = models.ImageField(upload_to='notices/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('notice_detail', kwargs={'pk': self.pk})
    
    def slug(self):
        return slugify(self.title)

class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    # created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)


class MessageReaction(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    emoji = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)


class UserStatus(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)

# =============== END OF NOTICE MODELS =========================================

# =============== START OF TIMETABLE MODELS =========================================

# Timetable models
class Timetable(models.Model):
    name = models.CharField(max_length=255, unique=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    level = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.course.name} ({self.level})"

class Session(models.Model):
    SESSION_TYPES = [
        ('Theory', 'Theory'),
        ('Lab', 'Lab'),
        ('Workshop', 'Workshop'),
        ('Industry', 'Industry Visit'),
    ]
    
    timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name='sessions')
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, blank=True, null=True)
    title = models.CharField(max_length=200)
    location = models.CharField(max_length=100)
    trainer = models.CharField(max_length=100)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    requirements = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.title} ({self.get_session_type_display()})"
        


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++






# -----------------------------------------------------
# MODELS TO STORE THE BOOLKS TYHAT THE USER LOVES MOST
# -----------------------------------------------------

# from django.db import models
# from django.contrib.auth.models import User

class LovedBook(models.Model):
    user = models.ForeignKey(Trainee, on_delete=models.CASCADE)
    google_id = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=150, blank=True, null=True)
    cover = models.URLField(blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.user.username})"


from django.db import models
from django.utils import timezone
from django.core.validators import FileExtensionValidator
# from trainee.models import Trainee  # your Trainee model

class Assignment(models.Model):
    title = models.CharField(max_length=200)
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    instructor_name = models.CharField(max_length=200)
    instructor_email = models.EmailField()
    description = models.TextField()
    instructions = models.TextField()
    learning_objectives = models.TextField(blank=True, null=True)
    rubric = models.TextField(blank=True, null=True)
    due_date = models.DateTimeField()
    max_points = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_active(self):
        return timezone.now() <= self.due_date

    def __str__(self):
        return f"{self.title} - {self.course.name}"


class Submission(models.Model):
    STATUS_CHOICES = [
        ('Not Submitted', 'Not Submitted'),
        ('Submitted', 'Submitted'),
        ('Graded', 'Graded'),
    ]

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    trainee = models.ForeignKey(Trainee, on_delete=models.CASCADE)
    file_upload = models.FileField(upload_to='submissions/', blank=True, null=True,
    validators=[FileExtensionValidator(['pdf','doc','docx','txt'])])
    short_text = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Not Submitted')
    grade = models.PositiveIntegerField(blank=True, null=True)
    admin_feedback = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('assignment', 'trainee')

    def __str__(self):
        return f"{self.assignment.title} - {self.trainee}"



# ----------------------------------------------------

# ATTENDANCE MODELS

# ----------------------------------------------------
# models.py
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class AttendanceRegister(models.Model):
    title = models.CharField(max_length=200, default="TeCade Attendance Form")
    date = models.DateField(default=timezone.now)
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    department = models.ForeignKey('Department', on_delete=models.CASCADE)
    time_from = models.TimeField()
    time_to = models.TimeField()
    trainer_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.course.name} ({self.date})"

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
        ('Excused', 'Excused'),
    ]
    
    register = models.ForeignKey(AttendanceRegister, on_delete=models.CASCADE, related_name="attendances")
    trainee = models.ForeignKey('Trainee', on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Absent')
    remark = models.TextField(blank=True, null=True)
    checked = models.BooleanField(default=False)  # For the checkbox in the admin form
    
    def __str__(self):
        return f"{self.trainee} - {self.status}"

class ExcuseRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    
    trainee = models.ForeignKey('Trainee', on_delete=models.CASCADE)
    date = models.DateField()
    session = models.CharField(max_length=20, choices=[
        ('morning', 'Morning Session'), 
        ('afternoon', 'Afternoon Session'), 
        ('full', 'Full Day')
    ])
    reason = models.TextField()
    supporting_docs = models.FileField(upload_to='excuse_docs/', blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    trainer_remark = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.trainee} - {self.date} - {self.status}"

# models.py
from django.contrib.auth.models import User

class Trainer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    courses = models.ManyToManyField('Course')
    
    def __str__(self):
        return f"{self.user.get_full_name()} (Trainer)" 


# ________________________________________________________________________________

# -----------------Models for Portfolio of evidence page--------------------------

# _________________________________________________________________________________

import uuid, os

def evidence_upload_path(instance, filename):
    # Generate unique filename
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('portfolio_evidence', filename)

class CompetencyCategory(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        verbose_name_plural = "Competency Categories"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name

class Competency(models.Model):
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('needs_review', 'Needs Review'),
        ('competent', 'Competent'),
    ]
    
    category = models.ForeignKey(CompetencyCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    criteria = models.TextField(help_text="Assessment criteria for this competency")
    order = models.IntegerField(default=0)
    
    class Meta:
        verbose_name_plural = "Competencies"
        ordering = ['category__order', 'order', 'name']
    
    def __str__(self):
        return f"{self.category.name}: {self.name}"

class EvidenceArtifact(models.Model):
    EVIDENCE_TYPES = [
        ('document', 'Document'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('certificate', 'Certificate'),
        ('reflection', 'Reflection'),
        ('feedback', 'Feedback'),
        ('other', 'Other'),
    ]
    
    trainee = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    evidence_type = models.CharField(max_length=20, choices=EVIDENCE_TYPES)
    file = models.FileField(upload_to=evidence_upload_path, blank=True, null=True)
    external_url = models.URLField(blank=True, null=True)
    competencies = models.ManyToManyField(Competency, blank=True)
    upload_date = models.DateTimeField(default=timezone.now)
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    
    # Metadata for evidence
    date_created = models.DateField(blank=True, null=True, help_text="When was this evidence created?")
    location = models.CharField(max_length=200, blank=True, help_text="Where was this evidence created?")
    
    class Meta:
        ordering = ['-upload_date']
    
    def __str__(self):
        return self.title
    
    def get_file_extension(self):
        if self.file:
            return os.path.splitext(self.file.name)[1][1:].upper()
        return None

class Assessment(models.Model):
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('needs_revision', 'Needs Revision'),
        ('approved', 'Approved'),
    ]
    
    evidence = models.ForeignKey(EvidenceArtifact, on_delete=models.CASCADE)
    assessor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assessments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    comments = models.TextField(blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    assessment_date = models.DateTimeField(default=timezone.now)
    feedback = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-assessment_date']
    
    def __str__(self):
        return f"Assessment of {self.evidence.title} by {self.assessor.get_full_name()}"

#============== reflecion page changes I changed reflection models --------------
class Reflection(models.Model):
    ASSESSMENT_TYPES = [
        ('cat', 'CAT'),
        ('exam', 'Final Exam'), 
        ('assignment', 'Assignment'),
        ('project', 'Project'),
        ('practical', 'Practical'),
        ('general', 'General Learning'),
    ]
    
    TERM_CHOICES = [
        ('term1', 'Term 1'),
        ('term2', 'Term 2'), 
        ('term3', 'Term 3'),
        ('semester1', 'Semester 1'),
        ('semester2', 'Semester 2'),
    ]
    
    trainee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    date = models.DateTimeField(default=timezone.now)
    
    # Simple char field for unit/course instead of ForeignKey for now
    unit_name = models.CharField(max_length=200, blank=True, help_text="Unit/Course name")
    unit_code = models.CharField(max_length=50, blank=True, help_text="Unit/Course code")
    
    term = models.CharField(max_length=20, choices=TERM_CHOICES, blank=True)
    assessment_type = models.CharField(max_length=20, choices=ASSESSMENT_TYPES, default='general')
    
    # These should work if EvidenceArtifact and Competency exist in home app
    related_evidence = models.ManyToManyField('EvidenceArtifact', blank=True)
    related_competencies = models.ManyToManyField('Competency', blank=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.title} - {self.trainee}"
    
    def get_assessment_type_display(self):
        return dict(self.ASSESSMENT_TYPES).get(self.assessment_type, self.assessment_type)
    
    def get_unit_display(self):
        if self.unit_code and self.unit_name:
            return f"{self.unit_code} - {self.unit_name}"
        return self.unit_name or self.unit_code or "No unit specified"

class PortfolioShare(models.Model):
    trainee = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Share link for {self.trainee.get_full_name()}"
    
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def can_access(self):
        return self.is_active and not self.is_expired()
        
      
# <<Dp_Academics >>

class TrainerData(models.Model):
    # Personal Information
    passport_image = models.ImageField(upload_to='trainer_passports/', null=True, blank=True)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=20)
    dob = models.DateField(null=True, blank=True)

    employer = models.CharField(max_length=50, null=True, blank=True)  # PSC / Board
    staff_number = models.CharField(max_length=100, null=True, blank=True)
    id_number = models.CharField(max_length=50, null=True, blank=True)
    phone = models.CharField(max_length=20)

    first_appointment = models.DateField(null=True, blank=True)
    current_appointment = models.DateField(null=True, blank=True)

    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True)

    current_jg = models.CharField(max_length=50, blank=True, null=True)  # Optional
    courses = models.CharField(max_length=500, blank=True, null=True)  # Store comma-separated IDs
    special_responsibilities = models.CharField(max_length=200, blank=True, null=True)

    # Next of Kin
    kin_name = models.CharField(max_length=200, null=True, blank=True)
    kin_phone = models.CharField(max_length=20, null=True, blank=True)
    kin_address = models.CharField(max_length=200, blank=True, null=True)
    kin_email = models.EmailField(blank=True, null=True)

    # Academic Documents
    tertiary_certificate = models.FileField(upload_to='trainer_docs/', null=True, blank=True)
    o_level_certificate = models.FileField(upload_to='trainer_docs/', null=True, blank=True)
    secondary_certificate = models.FileField(upload_to='trainer_docs/', null=True, blank=True)

    date_registered = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class TrainerOtherDocument(models.Model):
    trainer = models.ForeignKey(TrainerData, on_delete=models.CASCADE, related_name="other_docs")
    document = models.FileField(upload_to="trainer_others/")

    def __str__(self):
        return f"Other Document for {self.trainer.first_name} {self.trainer.last_name}"






