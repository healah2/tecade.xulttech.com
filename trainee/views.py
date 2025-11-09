from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from home.models import AdminIndex, CarouselSlide, AdminAbout, AdminInstitutionalManagement, AdminAcDpt, AdminNonAcDpt, Trainee
# Create your views here.
from django.shortcuts import render
from home.models import AdminIndex, CarouselSlide, AdminBom
from django.db.models import Count, Q
from django.http import JsonResponse
from django.db.models import Count
from home.models import Trainee, Course
from collections import defaultdict
from django.shortcuts import render, redirect
from django.contrib import messages
from home.models import AdminCredentials
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
from home.models import Trainee, Department, Course, Notice
from django.http import JsonResponse
from datetime import datetime
from django.contrib import messages
import re, random

# imports to handle the login loggic
from django.contrib.auth import login, authenticate
from django.contrib import messages
from home.models import Trainee
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.core.serializers.json import DjangoJSONEncoder
# from django.contrib.auth import login, authenticate
from django.contrib import messages
from home.models import Trainee
from .auth_backends import TraineeAuthBackend
import json
from django.shortcuts import render
from django.core.serializers.json import DjangoJSONEncoder
from home.models import Conversation, Notice, Trainee
from trainee.auth_backends import TraineeAuthBackend
from django.shortcuts import render
from django.core.serializers.json import DjangoJSONEncoder
from home.models import Conversation, Notice, Trainee
from trainee.auth_backends import TraineeAuthBackend
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from finance.models import FeeStatement
from home.models import TraineeSession, CurrentSession
from django.utils import timezone
from django.contrib import messages
from collections import defaultdict
from django.core.exceptions import ValidationError



def trainee_login(request):
    if request.method == 'POST':
        user_type = request.POST.get('user_type')  # 'trainee' or 'staff'
        # Trainee authentication
        if user_type == 'trainee':
            trainee_number = request.POST.get('trainee_number')
            password = request.POST.get('password')
            
            # Authenticate using our custom backend
            backend = TraineeAuthBackend()
            trainee = backend.authenticate(request, trainee_number=trainee_number, password=password)
            
            if trainee:
                # Log the trainee in
                login(request, trainee, backend='trainee.auth_backends.TraineeAuthBackend')
                return redirect('trainee:trainee_dashboard')
            else:
                messages.error(request, 'Invalid trainee number or password')
        
        # Staff authentication
        elif user_type == 'staff':
            email_or_id = request.POST.get('email') or request.POST.get('staff_id')
            password = request.POST.get('password')
            return redirect('staff_dashboard')
    
    return render(request, 'trainee/login.html')

from django.shortcuts import render, get_object_or_404
# from .models import Trainee

def portfolio_dashiboard(request):
    trainee = request.user 
    if request.user.is_authenticated:
        trainee = get_object_or_404(Trainee, trainee = request.user)
    return render(request, 'trainee/portfolio.html', {'trainee': trainee})


# @login_required (login_url='/trainee/trainee_login/')
# def trainee_profile(request):
#     return render(request, 'trainee/trainee_profile.html', {'trainee': request.user})

@login_required(login_url='/trainee/trainee_login/')
def trainee_change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Verify current password
        if not (request.user.check_password(current_password) or 
                current_password == request.user.trainee_number):
            messages.error(request, 'Current password is incorrect')
            return redirect('trainee_change_password')
        
        # Verify new passwords match
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match')
            return redirect('trainee_change_password')
        
        # Set new password
        request.user.set_password(new_password)
        request.user.save()
        
        # Update session to prevent logout
        update_session_auth_hash(request, request.user)
        
        messages.success(request, 'Your password has been updated successfully!')
        return redirect('trainee_login')
    
    return render(request, 'trainee/change_password.html')

def trainee_logout(request):
    logout(request)
    return redirect('home')

@login_required(login_url='trainee:trainee_login')
def trainee_dashboard(request):
    # Ensure user is authenticated
    if not request.user.is_authenticated:
        return redirect("trainee:trainee_login")
    
    trainee = request.user  
    current_session = CurrentSession.objects.filter(is_active=True).first()
    
    # Check if trainee is registered for current session
    is_registered = False
    current_trainee_session = None
    
    if current_session:
        current_trainee_session = TraineeSession.objects.filter(
            trainee=trainee,
            session_period=current_session.session_period
        ).first()
        is_registered = current_trainee_session is not None

    user_data = json.dumps({
        "id": trainee.id,
        "username": getattr(trainee, "full_name", f"{trainee.first_name} {trainee.last_name}")
    }, cls=DjangoJSONEncoder)

    # Shared conversation
    conversation = Conversation.objects.first()
    if not conversation:
        conversation = Conversation.objects.create()

    notices = Notice.objects.order_by('-created_at')

    return render(request, 'trainee/trainee_dashboard.html', {
        'trainee': trainee,
        'user_data': user_data,
        'conversation': conversation,
        'notices': notices,
        'is_registered': is_registered,
        'current_trainee_session': current_trainee_session,
        'current_session': current_session,
    })


@login_required(login_url='trainee:trainee_login')
def trainee_register_session(request):
    """Allow trainees to self-register for current session"""
    trainee = request.user
    warning = None
    errors = []
    success = None

    try:
        current_session = CurrentSession.objects.get(is_active=True)
    except CurrentSession.DoesNotExist:
        errors.append("No active session available. Please contact administration.")
        current_session = None

    if current_session:
        # Check if already registered
        if TraineeSession.objects.filter(
            trainee=trainee,
            session_period=current_session.session_period
        ).exists():
            warning = f"You are already registered for {current_session.session_period}."
        else:
            # Calculate next year/term
            last_session = TraineeSession.objects.filter(
                trainee=trainee
            ).order_by('-created_at').first()

            if last_session:
                year_of_study = int(last_session.year_of_study)
                term = int(last_session.term)
                if term < 3:
                    term += 1
                else:
                    term = 1
                    year_of_study += 1
            else:
                year_of_study, term = 1, 1

            # Create the session
            session = TraineeSession(
                trainee=trainee,
                current_session=current_session,
                session_period=current_session.session_period,
                year_of_study=year_of_study,
                term=term,
            )
            
            try:
                session.save()

                # Create FeeStatement DEBIT entry
                debit_payment_id = f"INV-DEBIT-{session.id}"
                FeeStatement.objects.create(
                    trainee=trainee,
                    transaction_type="DEBIT",
                    amount=session.fee_balance,
                    balance_after=session.fee_balance,
                    invoice_number=debit_payment_id,
                    reference=debit_payment_id,
                    session_period=session.session_period,
                    year_of_study=session.year_of_study,
                    term=session.term
                )

                success = f"Successfully registered for {current_session.session_period} (Year {year_of_study} Term {term}). You can now access all portal services!"
                
            except ValidationError as ve:
                for field, messages_list in ve.message_dict.items():
                    errors.extend(messages_list)

    context = {
        'trainee': trainee,
        'warning': warning,
        'errors': errors,
        'success': success,
        'current_session': current_session,
        'is_registered': TraineeSession.objects.filter(
            trainee=trainee,
            session_period=current_session.session_period if current_session else None
        ).exists() if current_session else False
    }
    return render(request, 'trainee/register_session.html', context)

@login_required(login_url='trainee:trainee_login')
def trainee_fee_statement(request):
    """Trainee view their own fee statement"""
    trainee = request.user
    current_session = CurrentSession.objects.filter(is_active=True).first()
    
    # Check if registered for current session
    if not current_session or not TraineeSession.objects.filter(
        trainee=trainee,
        session_period=current_session.session_period
    ).exists():
        messages.error(request, "You must be registered for the current accademic session to view your fee statement.")
        return redirect('trainee:trainee_dashboard')

    # Get fee statements for the trainee
    statements = FeeStatement.objects.filter(trainee=trainee).order_by("date")

    TERM_MAP = {'1': 'Term 1', '2': 'Term 2', '3': 'Term 3'}
    YEAR_MAP = {'1': 'First Year', '2': 'Second Year', '3': 'Third Year'}

    # Group by session
    grouped_statements = defaultdict(lambda: {"items": [], "termly_balance": 0})

    for stmt in statements:
        term_label = TERM_MAP.get(str(stmt.term), stmt.term)
        year_label = YEAR_MAP.get(str(stmt.year_of_study), stmt.year_of_study)
        session_label = f"{year_label} - {term_label}"

        grouped_statements[session_label]["items"].append(stmt)

    # Get latest balance for each session
    for session_label, data in grouped_statements.items():
        last_stmt = data["items"][-1]
        grouped_statements[session_label]["termly_balance"] = last_stmt.balance_after

    # Get current trainee session
    trainee_session = TraineeSession.objects.filter(trainee=trainee).order_by("-created_at").first()

    context = {
        "trainee": trainee,
        "trainee_session": trainee_session,
        "grouped_statements": grouped_statements.items(),
        "now": timezone.now(),
    }
    return render(request, "trainee/fee_statement.html", context)

# views.py
from django.shortcuts import render, redirect
from .forms import NoticeForm
from home .models import Notice

def upload_notice(request):
    if request.method == 'POST':
        form = NoticeForm(request.POST, request.FILES)
        if form.is_valid():
            saved_notice = form.save()
            return redirect('trainee:notice_detail', pk=saved_notice.pk)
    else:
        form = NoticeForm()
    
    return render(request, 'adminpages/upload_notice.html', {'form': form})

    

def notice_detail(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    other_notices = Notice.objects.exclude(pk=pk).order_by('-created_at')[:5]
    return render(request, 'notices/notice_detail.html', {
        'notice': notice,
        'other_notices': other_notices
    })    

def attendance(request):
    # For testing, get the first trainee
    trainee = Trainee.objects.first()
    if not trainee:
        # Create a test trainee if none exists
        trainee = Trainee.objects.create(
            trainee_number="TEST001",
            first_name="Test",
            last_name="Trainee",
            email="test@example.com"
        )
    
    context = {
        'trainee': trainee,
        'trainee_id': trainee.id
    }
    return render(request, 'stats/attendance.html', context)


from django.shortcuts import render, get_object_or_404
from home.models import LovedBook, Trainee
import requests


@login_required(login_url='trainee:trainee_login')
def library(request, trainee_id):
    trainee = get_object_or_404(Trainee, id=trainee_id)

    # get search params
    query = request.GET.get('q', '')
    department = request.GET.get('department', '')

    books = []

    if query:
        url = f"https://www.googleapis.com/books/v1/volumes?q={query}+subject:{department}"
        response = requests.get(url).json()

        for item in response.get("items", []):
            info = item.get("volumeInfo", {})
            books.append({
                "google_id": item["id"],
                "title": info.get("title", "No Title"),
                "author": ", ".join(info.get("authors", [])),
                "cover": info.get("imageLinks", {}).get("thumbnail", ""),
                "department": department or "General",
                "preview_link": info.get("previewLink"),  
            })

    context = {
        "trainee": trainee,
        "books": books,
        "search_query": query, 
        "borrowed_books": [],        
    }
    return render(request, 'stats/library.html', context)


@login_required(login_url='trainee:trainee_login')
def love_book(request, google_id):
    trainee = request.user
    # fetch details from Google Books
    url = f"https://www.googleapis.com/books/v1/volumes/{google_id}"
    response = requests.get(url).json()
    info = response.get("volumeInfo", {})

    LovedBook.objects.create(
        user=trainee,
        google_id=google_id,
        title=info.get("title", "No Title"),
        author=", ".join(info.get("authors", [])),
        cover=info.get("imageLinks", {}).get("thumbnail", ""),
        department=", ".join(info.get("categories", [])) if info.get("categories") else None
    )
    
    return redirect("trainee:library_detail", trainee_id=trainee.id)
    # return render ( request, 'stats/library.html', trainee_id=trainee.id)

# def assignment(request, trainee_id):
#     trainee = get_object_or_404(Trainee, id=trainee_id)
#     return render ( request, 'stats/assignments.html', {'trainee': trainee})




@login_required(login_url='/trainee/trainee_login/')
def traine_profile(request, trainee_id):
    trainee = get_object_or_404(Trainee, id=trainee_id)
    return render(request, 'trainee/trainee_profile.html', {'trainee': trainee})

# =================VIEWS FOR TIMETABLE STARTS HERE===========

from django.shortcuts import render, redirect, get_object_or_404
from home.models import Timetable, Session
from .forms import TimetableForm, SessionForm

def manage_timetable(request):
    timetables = Timetable.objects.all()
    
    if request.method == 'POST':
        form = TimetableForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('adminpages/manage_timetable')
    else:
        form = TimetableForm()
    
    return render(request, 'adminpages/timetable_admin.html', {
        'timetables': timetables,
        'form': form
    })

def edit_timetable(request, timetable_id):
    timetable = get_object_or_404(Timetable, id=timetable_id)
    
    # Get all courses for the dropdown
    courses = Course.objects.all()
    
    if request.method == 'POST':
        form = TimetableForm(request.POST, instance=timetable)
        if form.is_valid():
            form.save()
            messages.success(request, 'Timetable updated successfully!')
            return redirect('adminpages/manage_timetable')
    else:
        form = TimetableForm(instance=timetable)
    
    return render(request, 'adminpages/edit_timetable.html', {
        'timetable': timetable,
        'form': form,
        'courses': courses  # Make sure to pass courses to the template
    })

def delete_timetable(request, timetable_id):
    timetable = get_object_or_404(Timetable, id=timetable_id)
    timetable.delete()
    return redirect('adminpages/manage_timetable')

from django.shortcuts import render, get_object_or_404, redirect
from home.models import Timetable, Session
from .forms import SessionForm

def manage_sessions(request, timetable_id):
    timetable = get_object_or_404(Timetable, id=timetable_id)
    sessions = Session.objects.filter(timetable=timetable)

    if request.method == 'POST':
        form = SessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.timetable = timetable  # link session to timetable
            session.save()
            return redirect('trainee:manage_sessions', timetable_id=timetable.id)
    else:
        form = SessionForm()

    return render(request, 'adminpages/session_admin.html', {
        'timetable': timetable,
        'sessions': sessions,
        'form': form,
    })


def edit_session(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    
    if request.method == 'POST':
        form = SessionForm(request.POST, instance=session)
        if form.is_valid():
            form.save()
            return redirect('manage_sessions', timetable_id=session.timetable.id)
    else:
        form = SessionForm(instance=session)
    
    return render(request, 'adminpages/edit_session.html', {
        'session': session,
        'form': form
    })

def delete_session(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    timetable_id = session.timetable.id
    session.delete()
    return redirect('manage_sessions', timetable_id=timetable_id)    

from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render
from home.models import Trainee, Timetable, Session  # make sure these are imported


def timetable_view(request):
    # if not request.user.is_authenticated:
    #     return render(request, 'trainee/error.html', {
    #         'message': 'You must be logged in to view this page.'
    #     })

    # # Always resolve the logged-in user to a proper Trainee instance
    # try:
    #     # trainee = Trainee.objects.get(pk=request.user.pk)
    
    #      trainee = Trainee.objects.get(id_number=request.user.trainee_number)

    # except Trainee.DoesNotExist:
    #     return render(request, 'trainee/error.html', {
    #         'message': 'Access restricted to trainees only.'
    #     })
    trainee = request.user

    # Get timetable for trainee's course and level
    timetables = Timetable.objects.filter(
        course=trainee.course,
        level=trainee.course.level.replace("Level ", "")
    ).first()

    if not timetables:
        return render(request, 'stats/timetable.html', {
            'trainee': trainee,  # still pass trainee so base template doesn’t break
            'error': 'No timetable available yet for your course and level. '
                     'Keep checking or contact your course administration.'
        })

    # Get sessions for this timetable within the current week
    now = timezone.now()
    start_of_week = now - timedelta(days=now.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    sessions = Session.objects.filter(
        timetable=timetables,
        start_time__range=[start_of_week, end_of_week]
    ).order_by('start_time')

    # Group sessions by day and mark current sessions
    sessions_by_day = {}
    time_slots = set()

    for session in sessions:
        day = session.start_time.strftime('%A, %B %d')
        time_slot = f"{session.start_time.strftime('%H:%M')} - {session.end_time.strftime('%H:%M')}"
        session.is_current = (session.start_time <= now <= session.end_time)

        sessions_by_day.setdefault(day, []).append({
            'title': session.title,
            'session_type': session.session_type,
            'location': session.location,
            'trainer': session.trainer,
            'requirements': session.requirements,
            'start_time': session.start_time,
            'end_time': session.end_time,
            'time_slot': time_slot,
            'is_current': session.is_current,
        })
        time_slots.add(time_slot)

    # Convert time slots to sorted list
    time_slots = sorted(time_slots)

    return render(request, 'stats/timetable.html', {
        'trainee': trainee,  # always included for base template
        'timetables': timetables,
        'sessions_by_day': sessions_by_day,
        'time_slots': time_slots,
        'now': now
    })




# ____________________________________
# Added views________________________


@csrf_exempt
def tecade_bot(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message', '')
            image_data = data.get('image', None)
            
            # Prepare the request to Gemini API
            api_key = 'AIzaSyAq017UYKZjvSkIvu_gC7OsjjDAY2RiKYQ'
            url = f'https://generativelanguage.googleapis.com/v1beta/gemini-1.5-flash:generateContent?key={api_key}'
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": message
                    }]
                }]
            }
            
            if image_data:
                payload["contents"][0]["parts"].append({
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": image_data
                    }
                })
            
            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, json=payload, headers=headers)
            response_data = response.json()
            
            bot_response = response_data['candidates'][0]['content']['parts'][0]['text']
            
            return JsonResponse({'response': bot_response})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

# -------------------------ASSIGNMENTS---------------------
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from home.models import Assignment, Submission
from home.models import Trainee
from django.contrib.auth.decorators import login_required

# Helper function for template dictionary
def get_submissions_dict(trainee):
    subs = Submission.objects.filter(trainee=trainee)
    return {sub.assignment.id: sub for sub in subs}

# ---------------- Trainee Views ----------------
@login_required(login_url='trainee:trainee_login')
def assignment_list(request, trainee_id):
    # Get the trainee object
    trainee_obj = get_object_or_404(Trainee, id=trainee_id)
    # Trainee = request.user
    # Verify the logged-in user has access to this trainee's data
    # if request.user != trainee_obj.user:
    #     # Handle unauthorized access
    #     return redirect('trainee:trainee_dashboard')
    
    # Get assignments for the trainee's course
    assignments = Assignment.objects.filter(course=trainee_obj.course)
    submissions_dict = get_submissions_dict(trainee_obj)
    
    context = {
        'trainee': trainee_obj,  # Pass the actual trainee object
        'assignments': assignments, 
        'submissions_dict': submissions_dict,
        'current_user': trainee_id
    }
    return render(request, 'stats/assignments.html', context)





@login_required(login_url='trainee:trainee_login')
def submit_assignment(request, assignment_id):
    # Get the trainee object from the currently logged-in user
    try:
        # trainee = request.user
        trainee_obj = request.user
    except AttributeError:
        messages.error(request, "Trainee profile not found.")
        return redirect('trainee:trainee_dashboard')
    
    # Additional safety check
    if not trainee_obj:
        messages.error(request, "Trainee profile not found.")
        return redirect('trainee:trainee_dashboard')
    
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    # Check if due date passed
    if timezone.now() > assignment.due_date:
        messages.error(request, "Deadline passed. You cannot submit this assignment.")
        return redirect('trainee:assignment_list', trainee_id=trainee_obj.id)
    
    # Ensure only one submission
    submission, created = Submission.objects.get_or_create(
        assignment=assignment, 
        trainee=trainee_obj
    )

    if request.method == 'POST':
        file_upload = request.FILES.get('file_upload')
        short_text = request.POST.get('short_text')

        if not file_upload and not short_text:
            messages.error(request, "Please submit a file or enter text.")
            return redirect('trainee:assignment_list', trainee_id=trainee_obj.id)

        if file_upload:
            submission.file_upload = file_upload
        if short_text:
            submission.short_text = short_text
        
        submission.status = 'Submitted'
        submission.submitted_at = timezone.now()
        submission.save()
        
        messages.success(request, "Assignment submitted successfully.")
        return redirect('trainee:assignment_list', trainee_id=trainee_obj.id)

    # If it's a GET request, redirect to assignment list
    return redirect('trainee:assignment_list', trainee_id=trainee_obj.id)

# ---------------- Admin Views ----------------
@login_required
def admin_assignments(request):
    assignments = Assignment.objects.all().order_by('-due_date')
    context = {'assignments': assignments}
    return render(request, 'adminpages/admin_assignments.html', context)

@login_required
def create_assignment(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        course_id = request.POST.get('course')
        instructor_name = request.POST.get('instructor_name')
        instructor_email = request.POST.get('instructor_email')
        description = request.POST.get('description')
        instructions = request.POST.get('instructions')
        learning_objectives = request.POST.get('learning_objectives')
        rubric = request.POST.get('rubric')
        due_date = request.POST.get('due_date')
        max_points = request.POST.get('max_points')

        course = get_object_or_404(Course, id=course_id)

        Assignment.objects.create(
            title=title,
            course=course,
            instructor_name=instructor_name,
            instructor_email=instructor_email,
            description=description,
            instructions=instructions,
            learning_objectives=learning_objectives,
            rubric=rubric,
            due_date=due_date,
            max_points=max_points
        )
        messages.success(request, "Assignment created successfully.")
        return redirect('trainee:admin_assignments')

    courses = Course.objects.all()
    return render(request, 'adminpages/create_assignment.html', {'courses': courses})

@login_required
def view_submissions(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    submissions = Submission.objects.filter(assignment=assignment)
    return render(request, 'adminpages/view_submissions.html', {'assignment': assignment, 'submissions': submissions})

@login_required
def grade_submission(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    if request.method == 'POST':
        submission.grade = request.POST.get('grade')
        submission.admin_feedback = request.POST.get('feedback')
        submission.status = 'Graded'
        submission.save()
        messages.success(request, f"Submission for {submission.trainee} graded successfully.")
        return redirect('trainee:view_submissions', assignment_id=submission.assignment.id)
    return render(request, 'adminpages/grade_submission.html', {'submission': submission})


# ATTENDANCE VIEW

# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q
from home.models import AttendanceRegister, Attendance, Trainee, Course, Department, ExcuseRequest

# Remove the is_trainer function since we won't be using it for the dummy version

def create_register(request):
    # Get all courses for the dummy version
    courses = Course.objects.all()
    
    if request.method == "POST":
        course_id = request.POST.get("course")
        dept_id = request.POST.get("department")
            
        register = AttendanceRegister.objects.create(
            course_id=course_id,
            department_id=dept_id,
            date=request.POST.get("date"),
            time_from=request.POST.get("time_from"),
            time_to=request.POST.get("time_to"),
            trainer_name="Dummy Trainer",  # Hardcode trainer name for dummy version
        )

        # Auto populate trainees in this course/department
        trainees = Trainee.objects.filter(course_id=course_id, department_id=dept_id)
        for t in trainees:
            Attendance.objects.create(register=register, trainee=t)

        return redirect("trainee:mark_attendance", register_id=register.id)

    departments = Department.objects.all()
    return render(request, "adminpages/create_register.html", {
        "courses": courses, "departments": departments
    })

def mark_attendance(request, register_id):
    register = get_object_or_404(AttendanceRegister, id=register_id)
    attendances = register.attendances.select_related("trainee")

    if request.method == "POST":
        for att in attendances:
            status = request.POST.get(f"status_{att.id}")
            remark = request.POST.get(f"remark_{att.id}")
            checked = request.POST.get(f"checked_{att.id}") == 'on'
            
            att.status = status
            att.remark = remark
            att.checked = checked
            att.save()
            
        return redirect("trainee:trainer_dashboard")

    return render(request, "adminpages/mark_attendance.html", {
        "register": register, "attendances": attendances
    })

# views.py
# views.py
def trainer_dashboard(request):
    # Get registers created by this trainer
    # Use the trainee's full name instead of user's full name
    trainer_name = f"{request.user.first_name} {request.user.last_name}"
    registers = AttendanceRegister.objects.filter(trainer_name=trainer_name).order_by('-date')
    
    # Get pending excuse requests for trainees in the trainer's courses
    # Since we're using Trainee objects, we need to adjust this query
    # For now, let's get all pending requests (simplified for dummy version)
    excuse_requests = ExcuseRequest.objects.filter(status='Pending').select_related('trainee')
    
    # Calculate additional stats for the dashboard
    total_trainees = Trainee.objects.count()  # Simplified for dummy version
    total_courses = Course.objects.count()    # Simplified for dummy version
    
    return render(request, "adminpages/trainer_dashboard.html", {
        "registers": registers,
        "excuse_requests": excuse_requests,
        "total_trainees": total_trainees,
        "total_courses": total_courses,
    })


def handle_excuse_request(request, request_id):
    excuse_request = get_object_or_404(ExcuseRequest, id=request_id)
    
    # Verify the trainer teaches this trainee
    trainer_courses = Course.objects.filter(trainer=request.user)
    if not trainer_courses.filter(id=excuse_request.trainee.course.id).exists():
        return redirect('access_denied')
    
    if request.method == "POST":
        action = request.POST.get("action")
        remark = request.POST.get("trainer_remark")
        
        if action == "approve":
            excuse_request.status = "Approved"
            # Update attendance record if exists
            attendance = Attendance.objects.filter(
                register__date=excuse_request.date,
                trainee=excuse_request.trainee
            ).first()
            if attendance:
                attendance.status = "Excused"
                attendance.remark = f"Excused: {excuse_request.reason}"
                attendance.save()
                
        elif action == "reject":
            excuse_request.status = "Rejected"
            
        excuse_request.trainer_remark = remark
        excuse_request.save()
        
        return redirect("trainer_dashboard")
    
    return render(request, "adminpages/excuse_review.html", {
        "excuse_request": excuse_request
    })

# views.py (trainee section)
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from home.models import Attendance, ExcuseRequest, Trainee

@login_required
def trainee_attendance(request):
    try:
        trainee = Trainee.objects.get(user=request.user)
    except Trainee.DoesNotExist:
        return redirect('access_denied')
    
    # Get attendance records for this trainee
    attendance_records = Attendance.objects.filter(trainee=trainee).select_related('register').order_by('-register__date')
    
    # Calculate statistics
    total_records = attendance_records.count()
    present_count = attendance_records.filter(status='Present').count()
    absent_count = attendance_records.filter(status='Absent').count()
    late_count = attendance_records.filter(status='Late').count()
    excused_count = attendance_records.filter(status='Excused').count()
    
    overall_attendance = (present_count / total_records * 100) if total_records > 0 else 0
    
    # Get recent excuse requests
    excuse_requests = ExcuseRequest.objects.filter(trainee=trainee).order_by('-created_at')
    
    # Prepare data for charts
    # This would be more complex in a real implementation
    
    return render(request, "trainee/attendance.html", {
        "trainee": trainee,
        "attendance_records": attendance_records,
        "overall_attendance": overall_attendance,
        "present_count": present_count,
        "absent_count": absent_count,
        "late_count": late_count,
        "excused_count": excused_count,
        "excuse_requests": excuse_requests,
    })

@login_required
def submit_excuse_request(request):
    try:
        trainee = Trainee.objects.get(user=request.user)
    except Trainee.DoesNotExist:
        return JsonResponse({"success": False, "error": "Trainee not found"})
    
    if request.method == "POST":
        date = request.POST.get("date")
        session = request.POST.get("session")
        reason = request.POST.get("reason")
        
        excuse_request = ExcuseRequest.objects.create(
            trainee=trainee,
            date=date,
            session=session,
            reason=reason
        )
        
        # Handle file upload if present
        if 'supporting_docs' in request.FILES:
            excuse_request.supporting_docs = request.FILES['supporting_docs']
            excuse_request.save()
            
        return JsonResponse({"success": True, "request_id": excuse_request.id})
    
    return JsonResponse({"success": False, "error": "Invalid request method"})    


# views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
import calendar
from home.models import Attendance, ExcuseRequest, Trainee, AttendanceRegister

@login_required
def trainee_attendance_data(request):
    try:
        trainee = Trainee.objects.get(user=request.user)
    except Trainee.DoesNotExist:
        return JsonResponse({"error": "Trainee not found"}, status=404)
    
    # Get last update timestamp from request
    last_update = request.GET.get('last_update')
    
    # Get attendance records
    attendance_records = Attendance.objects.filter(trainee=trainee).select_related('register')
    
    if last_update:
        # Only get records updated since last check
        try:
            last_update_dt = timezone.datetime.fromisoformat(last_update.replace('Z', '+00:00'))
            attendance_records = attendance_records.filter(
                Q(updated_at__gt=last_update_dt) | Q(register__updated_at__gt=last_update_dt)
            )
        except (ValueError, AttributeError):
            pass
    
    attendance_records = attendance_records.order_by('-register__date')

    # Calculate statistics
    total_records = attendance_records.count()
    present_count = attendance_records.filter(status='Present').count()
    absent_count = attendance_records.filter(status='Absent').count()
    late_count = attendance_records.filter(status='Late').count()
    excused_count = attendance_records.filter(status='Excused').count()
    
    overall_attendance = (present_count / total_records * 100) if total_records > 0 else 0
    
    # Calculate monthly attendance (current month)
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    next_month = month_start + timedelta(days=32)
    month_end = next_month.replace(day=1) - timedelta(days=1)
    
    monthly_records = attendance_records.filter(
        register__date__gte=month_start,
        register__date__lte=month_end
    )
    monthly_total = monthly_records.count()
    monthly_present = monthly_records.filter(status='Present').count()
    monthly_attendance = (monthly_present / monthly_total * 100) if monthly_total > 0 else 0
    
    # Calculate absences left (assuming 10 allowed absences)
    total_allowable_absences = 10
    absences_remaining = max(0, total_allowable_absences - absent_count)
    
    # Prepare attendance history for the table
    attendance_history = []
    for record in attendance_records[:50]:  # Limit to 50 records for performance
        attendance_history.append({
            "date": record.register.date.strftime("%Y-%m-%d"),
            "day": record.register.date.strftime("%A"),
            "session": f"{record.register.time_from.strftime('%H:%M')} - {record.register.time_to.strftime('%H:%M')}",
            "check_in": "N/A",  # You might need to add these fields to your model
            "check_out": "N/A",  # You might need to add these fields to your model
            "status": record.status,
            "trainer": record.register.trainer_name,
        })
    
    # Generate notifications
    notifications = []
    if overall_attendance < 80:
        notifications.append({
            "level": "info",
            "icon": "info",
            "title": "Notice!",
            "message": "Your overall attendance is below 80%."
        })
    
    if monthly_attendance < 80:
        notifications.append({
            "level": "warning",
            "icon": "exclamation-triangle",
            "title": "Warning!",
            "message": "Your attendance for this month is below 80%."
        })
    
    if absences_remaining <= 2:
        notifications.append({
            "level": "danger",
            "icon": "exclamation-circle",
            "title": "Critical!",
            "message": f"You only have {absences_remaining} absences remaining."
        })
    
    # Prepare chart data
    # Monthly trend data (last 6 months)
    trend_labels = []
    trend_values = []
    
    for i in range(5, -1, -1):
        month = now.month - i
        year = now.year
        if month <= 0:
            month += 12
            year -= 1
        
        month_start = timezone.datetime(year, month, 1)
        _, last_day = calendar.monthrange(year, month)
        month_end = timezone.datetime(year, month, last_day)
        
        month_records = attendance_records.filter(
            register__date__gte=month_start,
            register__date__lte=month_end
        )
        month_total = month_records.count()
        month_present = month_records.filter(status='Present').count()
        month_attendance = (month_present / month_total * 100) if month_total > 0 else 0
        
        trend_labels.append(month_start.strftime("%b"))
        trend_values.append(round(month_attendance))
    
    # Attendance distribution for pie chart
    distribution_labels = ["Present", "Absent", "Late", "Excused"]
    distribution_values = [present_count, absent_count, late_count, excused_count]

    has_updates = attendance_records.exists() if last_update else True    
    # Get recent excuse requests
    excuse_requests = ExcuseRequest.objects.filter(trainee=trainee).order_by('-created_at')[:5]
    excuse_list = []
    for req in excuse_requests:
        excuse_list.append({
            "date": req.date.strftime("%Y-%m-%d"),
            "session": req.get_session_display(),
            "reason": req.reason,
            "status": req.status,
            "created_at": req.created_at.strftime("%Y-%m-%d %H:%M"),
        })
    
        return JsonResponse({
        "stats": {
            "overall": round(overall_attendance),
            "monthly": round(monthly_attendance),
            "absences_remaining": absences_remaining,
            "total_allowable_absences": total_allowable_absences,
            "late_count": late_count,
            "present_count": present_count,
            "absent_count": absent_count,
            "excused_count": excused_count,
        },
        "history": attendance_history,
        "notifications": notifications,
        "charts": {
            "trend": {
                "labels": trend_labels,
                "values": trend_values
            },
            "distribution": {
                "labels": distribution_labels,
                "values": distribution_values
            }
        },
        "excuse_requests": excuse_list,
        "last_update": timezone.now().isoformat(),
        "has_updates": has_updates
    })


@login_required
def trainee_attendance_calendar(request):
    try:
        trainee = Trainee.objects.get(user=request.user)
    except Trainee.DoesNotExist:
        return JsonResponse({"error": "Trainee not found"}, status=404)
    
    # Get start and end dates from request parameters
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    
    # Get attendance records for this trainee within the date range
    attendance_records = Attendance.objects.filter(trainee=trainee)
    
    if start_date and end_date:
        attendance_records = attendance_records.filter(
            register__date__gte=start_date,
            register__date__lte=end_date
        )
    
    attendance_records = attendance_records.select_related('register').order_by('register__date')
    
    # Prepare events for FullCalendar
    events = []
    for record in attendance_records:
        # Determine color based on status
        color_map = {
            'Present': '#00a65a',  # Green
            'Absent': '#dd4b39',   # Red
            'Late': '#f39c12',     # Yellow
            'Excused': '#00c0ef',  # Blue
        }
        
        color = color_map.get(record.status, '#777')
        
        events.append({
            "title": record.status,
            "start": record.register.date.isoformat(),
            "color": color,
            "description": f"Session: {record.register.time_from.strftime('%H:%M')} - {record.register.time_to.strftime('%H:%M')}<br>Trainer: {record.register.trainer_name}",
            "allDay": True
        })
    
    return JsonResponse({"events": events})

@login_required
def submit_excuse_request(request):
    try:
        trainee = Trainee.objects.get(user=request.user)
    except Trainee.DoesNotExist:
        return JsonResponse({"success": False, "error": "Trainee not found"})
    
    if request.method == "POST":
        date = request.POST.get("date")
        session = request.POST.get("session")
        reason = request.POST.get("reason")
        
        # Validate required fields
        if not all([date, session, reason]):
            return JsonResponse({"success": False, "error": "Missing required fields"})
        
        try:
            excuse_request = ExcuseRequest.objects.create(
                trainee=trainee,
                date=date,
                session=session,
                reason=reason
            )
            
            # Handle file upload if present
            if 'supporting_docs' in request.FILES:
                excuse_request.supporting_docs = request.FILES['supporting_docs']
                excuse_request.save()
                
            return JsonResponse({"success": True, "request_id": excuse_request.id})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    
    return JsonResponse({"success": False, "error": "Invalid request method"})    



    from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

@require_GET
def trainee_attendance_data(request):
    return JsonResponse({
        "stats": {
            "overall": 90,
            "monthly": 95,
            "absences_remaining": 2,
            "total_allowable_absences": 5,
            "late_count": 1
        },
        "history": [
            {"date": "2025-08-28", "day": "Monday", "session": "Morning", "check_in": "08:05", "check_out": "12:00", "status": "Present", "trainer": "Mr. Smith"},
            {"date": "2025-08-29", "day": "Tuesday", "session": "Afternoon", "check_in": "14:05", "check_out": "17:00", "status": "Late", "trainer": "Mr. Smith"},
        ],
        "notifications": [],
        "charts": {
            "trend": {"labels": ["Jan", "Feb"], "values": [85, 90]},
            "distribution": {"labels": ["Present", "Absent", "Late", "Excused"], "values": [20, 2, 1, 3]}
        }
    })

@require_GET
def trainee_attendance_calendar(request):
    return JsonResponse({
        "events": [
            {"title": "Present", "start": "2025-08-28", "description": "Morning session"},
            {"title": "Late", "start": "2025-08-29", "description": "Afternoon session"}
        ]
    })

@require_POST
def submit_excuse_request(request):
    return JsonResponse({"status": "ok", "message": "Excuse request submitted"})


# ________________________________________________________
# __________PORT FOLIO OF EVITENCE VIEWS__________________
# ________________________________________________________

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.core.paginator import Paginator
from home.models import *
import json

from home.models import Trainee, Competency, EvidenceArtifact, Reflection, PortfolioShare, Assessment 
from django.contrib.auth import get_user_model

@login_required(login_url='/trainee/trainee_login/')
def portfolio_dashboard(request):
    user = request.user
    User = get_user_model()

    # Detect trainee instance
    if hasattr(user, 'trainee_profile'):
        trainee = user.trainee_profile
        trainee_user = user
    elif isinstance(user, Trainee):
        trainee = user
        trainee_user, _ = User.objects.get_or_create(
            username=trainee.trainee_number,
            defaults={
                'first_name': trainee.first_name,
                'last_name': trainee.last_name,
                'email': trainee.email,
                'password': trainee.trainee_number,
            },
        )
    else:
        trainee = getattr(user, 'trainee_profile', None)
        trainee_user = user

    # ===== Portfolio Data =====
    competencies = Competency.objects.select_related('category').all()

    # Count trainee's evidence
    evidence_items = EvidenceArtifact.objects.filter(trainee=trainee_user)
    evidence_count = evidence_items.count()
    target_evidence = 50

    # Calculate competency progress
    competency_status = {}
    for comp in competencies:
        has_evidence = evidence_items.filter(competencies=comp).exists()
        competency_status[comp.id] = 'competent' if has_evidence else 'in-progress'

    # Count competencies achieved
    achieved_count = sum(1 for s in competency_status.values() if s == 'competent')
    target_competencies = 20

    # Assessments
    recent_assessments = Assessment.objects.filter(
        evidence__trainee=trainee_user
    ).select_related('evidence', 'assessor').order_by('-assessment_date')[:5]

    # Evidence
    recent_evidence = evidence_items.order_by('-upload_date')[:5]

    # Share Link
    share = PortfolioShare.objects.filter(trainee=trainee_user, is_active=True).first()
    share_link = (
        request.build_absolute_uri(
            reverse('trainee:portfolio_shared', kwargs={'token': share.token})
        )
        if share and share.can_access()
        else None
    )

    context = {
        'trainee': trainee,
        'competencies': competencies,
        'competency_status': competency_status,
        'recent_evidence': recent_evidence,
        'recent_assessments': recent_assessments,
        'share_link': share_link,
        'evidence_count': evidence_count,
        'target_evidence': target_evidence,
        'achieved_count': achieved_count,
        'target_competencies': target_competencies,
    }

    return render(request, 'trainee/portfolio_main.html', context)



@login_required(login_url='/trainee/trainee_login/')
def portfolio_evidence(request):
    # Get the appropriate user object based on authentication backend
    # if isinstance(request.user, Trainee):
    #     # User is authenticated via TraineeAuthBackend (Trainee instance)
    #     trainee_user = get_user_model().objects.get(username=request.user.trainee_number)
    # else:
    #     # User is authenticated via default backend (User instance)
    #     trainee_user = request.user

    user = request.user
    User = get_user_model()

    # Detect trainee instance
    if hasattr(user, 'trainee_profile'):
        trainee = user.trainee_profile
        trainee_user = user
    elif isinstance(user, Trainee):
        trainee = user
        trainee_user, _ = User.objects.get_or_create(
            username=trainee.trainee_number,
            defaults={
                'first_name': trainee.first_name,
                'last_name': trainee.last_name,
                'email': trainee.email,
                'password': trainee.trainee_number,
            },
        )
    else:
        trainee = getattr(user, 'trainee_profile', None)
        trainee_user = user
    
    # Get evidence for the trainee
    evidence_list = EvidenceArtifact.objects.filter(trainee=trainee_user).order_by('-upload_date')
    
    # Filtering
    evidence_type = request.GET.get('type', '')
    if evidence_type:
        evidence_list = evidence_list.filter(evidence_type=evidence_type)
    
    competency_id = request.GET.get('competency', '')
    if competency_id:
        evidence_list = evidence_list.filter(competencies__id=competency_id)
    
    search_query = request.GET.get('q', '')
    if search_query:
        evidence_list = evidence_list.filter(
            models.Q(title__icontains=search_query) |
            models.Q(description__icontains=search_query) |
            models.Q(tags__icontains=search_query)
        )
    
    # evidence_type_counts = {}
    # for type_value, type_name in EvidenceArtifact.EVIDENCE_TYPES:
    #     count = EvidenceArtifact.objects.filter(
    #         trainee=request.user, 
    #         evidence_type=type_value
    #     ).count()
    #     evidence_type_counts[type_value] = count

    # Pagination
    paginator = Paginator(evidence_list, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    evidence_types = EvidenceArtifact.EVIDENCE_TYPES
    competencies = Competency.objects.all()
    
    context = {
        'page_obj': page_obj,
        'evidence_types': evidence_types,
        'competencies': competencies,
        'current_type': evidence_type,
        'current_competency': competency_id,
        'search_query': search_query,
        'trainee': trainee_user,
        # 'evidence_type_counts': evidence_type_counts,
        'trainee': trainee,
    }
    
    return render(request, 'trainee/evidence.html', context)

@login_required(login_url='/trainee/trainee_login/')
def portfolio_upload(request):
    # Get the appropriate user object based on authentication backend
    # if isinstance(request.user, Trainee):
    #     # User is authenticated via TraineeAuthBackend (Trainee instance)
    #     trainee_user = get_user_model().objects.get(username=request.user.trainee_number)
    # else:
    #     # User is authenticated via default backend (User instance)
    #     trainee_user = request.user

    user = request.user
    User = get_user_model()

    # Detect trainee instance
    if hasattr(user, 'trainee_profile'):
        trainee = user.trainee_profile
        trainee_user = user
    elif isinstance(user, Trainee):
        trainee = user
        trainee_user, _ = User.objects.get_or_create(
            username=trainee.trainee_number,
            defaults={
                'first_name': trainee.first_name,
                'last_name': trainee.last_name,
                'email': trainee.email,
                'password': trainee.trainee_number,
            },
        )
    else:
        trainee = getattr(user, 'trainee_profile', None)
        trainee_user = user

    if request.method == 'POST':
        # Process form data
        title = request.POST.get('title')
        description = request.POST.get('description')
        evidence_type = request.POST.get('evidence_type')
        competency_ids = request.POST.getlist('competencies')
        tags = request.POST.get('tags')
        
        # Create evidence artifact
        evidence = EvidenceArtifact(
            trainee=trainee_user,
            title=title,
            description=description,
            evidence_type=evidence_type,
            tags=tags
        )
        
        # Handle file upload
        if 'file' in request.FILES:
            evidence.file = request.FILES['file']

        evidence.save()  # This line and everything below should be indented to be inside the POST block

        # FIX: Parse competency_ids properly before the loop
        competency_ids = request.POST.getlist('competencies')
        # If we got a single string with commas, split it
        if len(competency_ids) == 1 and ',' in competency_ids[0]:
            competency_ids = competency_ids[0].split(',')

        # Now process each competency ID
        for competency_id in competency_ids:
            try:
                # Clean the ID - remove whitespace and convert to integer
                clean_id = int(competency_id.strip())
                competency = Competency.objects.get(id=clean_id)
                evidence.competencies.add(competency)
            except (ValueError, TypeError):
                print(f"Invalid competency ID: {competency_id}")
            except Competency.DoesNotExist:
                print(f"Competency not found: {competency_id}")

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Handle Dropzone AJAX upload
            return JsonResponse({'success': True, 'message': 'Evidence uploaded successfully'})
        else:
            # Handle traditional form submission
            return redirect('portfolio_evidence')
    
    # GET request - show form (this part only runs for GET requests)
    competencies = Competency.objects.all()
    evidence_types = EvidenceArtifact.EVIDENCE_TYPES
    
    context = {
        'competencies': competencies,
        'evidence_types': evidence_types,
        'trainee': trainee_user,
        'trainee': trainee,   
    }
    
    return render(request, 'trainee/upload.html', context)


@login_required(login_url='/trainee/trainee_login/')
def portfolio_reflections(request):
    # Get the appropriate user object based on authentication backend
    if isinstance(request.user, Trainee):
        trainee_user = get_user_model().objects.get(username=request.user.trainee_number)
        
        trainee_obj = request.user
    else:
        trainee_user = request.user
        trainee_obj = getattr(request.user, 'trainee_profile', None)

    # Handle POST request (form submission)
    if request.method == 'POST':
        try:
            title = request.POST.get('title', '').strip()
            content = request.POST.get('content', '').strip()
            unit_name = request.POST.get('unit_name', '').strip()
            unit_code = request.POST.get('unit_code', '').strip()
            term = request.POST.get('term', '')
            assessment_type = request.POST.get('assessment_type', 'general')
            evidence_ids = request.POST.getlist('related_evidence')
            
            if not title or not content:
                messages.error(request, 'Title and content are required.')
            else:
                reflection = Reflection(
                    trainee=trainee_user,
                    title=title,
                    content=content,
                    unit_name=unit_name,
                    unit_code=unit_code,
                    term=term,
                    assessment_type=assessment_type
                )
                
                reflection.save()
                
                # Link evidence if provided
                for evidence_id in evidence_ids:
                    try:
                        evidence = EvidenceArtifact.objects.get(id=evidence_id, trainee=trainee_user)
                        reflection.related_evidence.add(evidence)
                    except EvidenceArtifact.DoesNotExist:
                        continue
                
                messages.success(request, 'Reflection created successfully!')
                return redirect('trainee:portfolio_reflections')  # Redirect to clear form
                
        except Exception as e:
            messages.error(request, f'Error creating reflection: {str(e)}')

    # GET request - display reflections
    reflections = Reflection.objects.filter(trainee=trainee_user).order_by('-date')
    
    # Get recent evidence for linking
    recent_evidence = EvidenceArtifact.objects.filter(trainee=trainee_user).order_by('-upload_date')[:10]
    
    # Get unique units from reflections for statistics
    reflection_stats = {
        'units': Reflection.objects.filter(trainee=trainee_user).exclude(unit_name='').values('unit_name', 'unit_code').annotate(
            reflection_count=Count('id')
        )
    }
    
    # Pagination
    paginator = Paginator(reflections, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'trainee': trainee_obj,
        'recent_evidence': recent_evidence,
        'reflection_stats': reflection_stats,
        'now': timezone.now(),
        'term_choices': Reflection.TERM_CHOICES,
        'assessment_choices': Reflection.ASSESSMENT_TYPES,
    }
    
    return render(request, 'trainee/reflections.html', context)

@login_required(login_url='/trainee/trainee_login/')
def edit_reflection(request, reflection_id):
    try:
        # Get the appropriate user object based on authentication backend (same as portfolio_reflections)
        if isinstance(request.user, Trainee):
            trainee_user = get_user_model().objects.get(username=request.user.trainee_number)
        else:
            trainee_user = request.user

        # Get the reflection and ensure it belongs to the current user
        reflection = Reflection.objects.get(id=reflection_id, trainee=trainee_user)
        
        if request.method == 'POST':
            # Update reflection with new data
            reflection.title = request.POST.get('title', '').strip()
            reflection.content = request.POST.get('content', '').strip()
            reflection.unit_name = request.POST.get('unit_name', '').strip()
            reflection.unit_code = request.POST.get('unit_code', '').strip()
            reflection.term = request.POST.get('term', '')
            reflection.assessment_type = request.POST.get('assessment_type', 'general')
            
            # Update related evidence
            evidence_ids = request.POST.getlist('related_evidence')
            reflection.related_evidence.clear()
            for evidence_id in evidence_ids:
                try:
                    evidence = EvidenceArtifact.objects.get(id=evidence_id, trainee=trainee_user)
                    reflection.related_evidence.add(evidence)
                except EvidenceArtifact.DoesNotExist:
                    continue
            
            reflection.save()
            messages.success(request, 'Reflection updated successfully!')
            return redirect('trainee:portfolio_reflections')
        
        # For GET request, show the form with current data
        recent_evidence = EvidenceArtifact.objects.filter(trainee=trainee_user).order_by('-upload_date')[:10]
        
        context = {
            'trainee': trainee_user,
            'reflection': reflection,
            'recent_evidence': recent_evidence,
            'term_choices': Reflection.TERM_CHOICES,
            'assessment_choices': Reflection.ASSESSMENT_TYPES,
        }
        return render(request, 'trainee/edit_reflection.html', context)
        
    except Reflection.DoesNotExist:
        messages.error(request, 'Reflection not found or you do not have permission to edit it.')
        return redirect('trainee:portfolio_reflections')


@login_required(login_url='/trainee/trainee_login/')
def portfolio_share(request):
    user = request.user
    User = get_user_model()

    # Detect trainee instance
    if hasattr(user, 'trainee_profile'):
        trainee = user.trainee_profile
        trainee_user = user
    elif isinstance(user, Trainee):
        trainee = user
        trainee_user, _ = User.objects.get_or_create(
            username=trainee.trainee_number,
            defaults={
                'first_name': trainee.first_name,
                'last_name': trainee.last_name,
                'email': trainee.email,
                'password': trainee.trainee_number,
            },
        )
    else:
        trainee = getattr(user, 'trainee_profile', None)
        trainee_user = user
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create':
            # Create new share link
            expires_days = int(request.POST.get('expires', 30))
            expires_at = timezone.now() + timezone.timedelta(days=expires_days)
            
            # Deactivate any existing shares
            PortfolioShare.objects.filter(trainee=trainee_user).update(is_active=False)
            
            # Create new share
            share = PortfolioShare.objects.create(
                
                trainee = trainee_user,
                expires_at=expires_at
            )
            
        elif action == 'deactivate':
            # Deactivate current share
            PortfolioShare.objects.filter(trainee = trainee_user).update(is_active=False)
    
    # Get current share status
    current_share = PortfolioShare.objects.filter(trainee = trainee_user, is_active=True).first()
    share_link = None
    if current_share and current_share.can_access():
        share_link = request.build_absolute_uri(
            reverse('trainee:portfolio_shared', kwargs={'token': current_share.token})
        )
    
    context = {
        'current_share': current_share,
        'share_link': share_link,
        'trainee': trainee_user,
        'trainee': trainee,
    }
    
    return render(request, 'trainee/share.html', context)


def portfolio_shared(request, token):
    user = request.user
    User = get_user_model()

    # Detect trainee instance
    if hasattr(user, 'trainee_profile'):
        trainee = user.trainee_profile
        trainee_user = user
    elif isinstance(user, Trainee):
        trainee = user
        trainee_user, _ = User.objects.get_or_create(
            username=trainee.trainee_number,
            defaults={
                'first_name': trainee.first_name,
                'last_name': trainee.last_name,
                'email': trainee.email,
                'password': trainee.trainee_number,
            },
        )
    else:
        trainee = getattr(user, 'trainee_profile', None)
        trainee_user = user

    try:
        share = PortfolioShare.objects.get(token=token)
        
        if not share.can_access():
            raise Http404("This shared link is no longer active request the user for another Link")
        
        trainee = share.trainee
        
        # Get portfolio data for this trainee
        evidence_list = EvidenceArtifact.objects.filter(trainee=trainee).order_by('-upload_date')
        reflections = Reflection.objects.filter(trainee=trainee).order_by('-date')
        assessments = Assessment.objects.filter(evidence__trainee=trainee).select_related('evidence', 'assessor')
        
        # Get competencies with status
        competencies = Competency.objects.all().select_related('category')
        competency_status = {}
        for competency in competencies:
            evidence_count = EvidenceArtifact.objects.filter(
                trainee=trainee, 
                competencies=competency
            ).count()
            
            if evidence_count == 0:
                status = 'not_started'
            else:
                competent_assessments = Assessment.objects.filter(
                    evidence__trainee=trainee,
                    evidence__competencies=competency,
                    status='approved'
                ).exists()
                
                if competent_assessments:
                    status = 'competent'
                else:
                    under_review = Assessment.objects.filter(
                        evidence__trainee=trainee,
                        evidence__competencies=competency
                    ).exclude(status='submitted').exists()
                    
                    status = 'under_review' if under_review else 'in_progress'
            
            competency_status[competency.id] = status
        
        context = {
            'trainee': trainee,
            'trainer_user': trainee,    
            'evidence_list': evidence_list,
            'reflections': reflections,
            'assessments': assessments,
            'competencies': competencies,
            'competency_status': competency_status,
            'is_shared_view': True,
        }
        
        return render(request, 'trainee/shared_view.html', context)
    
    except PortfolioShare.DoesNotExist:
        raise Http404("Invalid share link")