from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from .models import AdminIndex, CarouselSlide, AdminAbout, AdminInstitutionalManagement, AdminAcDpt, AdminNonAcDpt, Trainee
# Create your views here.
from django.shortcuts import render
from .models import AdminIndex, CarouselSlide, AdminBom
from django.db.models import Count, Q
from django.http import JsonResponse
from django.db.models import Count
from .models import Trainee, Course, TraineeSession
from collections import defaultdict
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import AdminCredentials
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
from .models import Trainee, Department, Course
from django.http import JsonResponse
from datetime import datetime
from django.contrib import messages
import re
from django.utils import timezone
from . import home_global_views
from .models import CurrentSession
from django.shortcuts import render
from django.utils import timezone
from .models import TraineeSession, CurrentSession
from django.shortcuts import render
from django.core.exceptions import ValidationError
from .models import Trainee, TraineeSession, CurrentSession
from finance.models import FeeStatement 

def home(request):
    # Fetch the single AdminIndex instance (assuming only one is used)
    admin_data = AdminIndex.objects.first()

    # Get the carousel slides associated with that AdminIndex
    slides = CarouselSlide.objects.filter(admin_index=admin_data).order_by('order')

    # Prepare fact items for looping in the template
    fact_items = []
    if admin_data:
        fact_items = [
            {
                'title': 'Partner Institutions',
                'count': admin_data.num_institutions,
                'icon_class': 'fa fa-university',
                'bg_color': 'bg-primary'
            },
            {
                'title': 'Trainees Managed',
                'count': admin_data.num_trainees,
                'icon_class': 'fa fa-user-graduate',
                'bg_color': 'bg-light'
            },
            {
                'title': 'Trainers Engaged',
                'count': admin_data.num_trainers,
                'icon_class': 'fa fa-chalkboard-teacher',
                'bg_color': 'bg-primary'
            }
        ]

    return render(request, 'clientside/index.html', {
        'slides': slides,
        'fact_items': fact_items
    })


def about(request):
    return render(request, 'clientside/about.html')

def contact(request):
    return render(request, 'clientside/contact.html')


def trainee_dashboard(request):
    return render(request, 'trainee/trainee_dashboard.html')

# def staff_dashboard(request):
#     return render(request, 'staff/staff_dashboard.html')

def mailbox(request):
    return render(request, 'mailbox.html')

def simple_tables(request):
    return render(request, 'simple_tables.html')

def data_tables(request):
    return render(request, 'data_tables.html')

def login(request):
    if request.method == 'POST':
        user_type = request.POST.get('user_type')  # 'trainee' or 'staff'

        # You can also fetch and process credentials here
        email_or_id = request.POST.get('email') or request.POST.get('staff_id')
        password = request.POST.get('password')

        # redirecting based on form type
        if user_type == 'trainee':
            return redirect('trainee_dashboard')
        elif user_type == 'staff':
            return redirect('staff_dashboard')

    return render(request, 'logins/login.html')

def academic_departments(request):
    departments = AdminAcDpt.objects.all()
    return render(request, 'clientside/academic_departments.html', {'departments': departments})

def non_academic(request):
    departments = AdminNonAcDpt.objects.all()
    return render(request, 'clientside/non_academic.html', {'departments': departments})

def academic_dpt_details(request, pk):
    dept = get_object_or_404(AdminAcDpt, pk=pk)
    return render(request, 'clientside/academic_dpt_details.html', {'dept': dept})

def non_academic_details(request, pk):
    dept = get_object_or_404(AdminNonAcDpt, pk=pk)
    return render(request, 'clentside/non_academic_details.html', {'dept': dept})

def academic_courses(request):
    return render(request, 'clientside/academic_courses.html')

def bom(request):
    bom_members = AdminBom.objects.all()
    return render(request, 'clientside/bom.html', {'bom_members': bom_members})

def institutional(request):
    team_members = AdminInstitutionalManagement.objects.all()
    return render(request, 'clientside/institutional.html', {'team_members': team_members})

def apply_levels(request):
    return render(request, 'clientside/apply_levels.html')

def apply_departments(request):
    departments = AdminAcDpt.objects.all()
    return render(request, 'clientside/apply_departments.html', {'departments': departments})

def apply_courses(request, pk):
    dept = get_object_or_404(AdminAcDpt, pk=pk)  # or AdminAcDpt
    return render(request, 'clientside/apply_courses.html', {'dept': dept})

def heads_of_departments(request):
    return render(request, 'clientside/heads_of_departments.html')


def admin_index(request):
    admin_data, created = AdminIndex.objects.get_or_create(pk=1)

    if request.method == 'POST':
        # Update Facts Section
        admin_data.num_institutions = request.POST.get('partners', admin_data.num_institutions)
        admin_data.num_trainees = request.POST.get('trainees', admin_data.num_trainees)
        admin_data.num_trainers = request.POST.get('trainers', admin_data.num_trainers)
        admin_data.save()

        # Handle new Carousel Slide addition
        image = request.FILES.get('carousel_image')
        subtitle = request.POST.get('carousel_subtitle')
        title = request.POST.get('carousel_title')

        if image and subtitle and title:
            CarouselSlide.objects.create(
                admin_index=admin_data,
                image=image,
                heading=title,
                subheading=subtitle
            )

        return redirect('admin_index')

    slides = CarouselSlide.objects.filter(admin_index=admin_data).order_by('order')

    return render(request, 'adminpages/admin_index.html', {
    'admin_data': admin_data,
    'adminindex_items': [admin_data],  # <-- make it a list so the template can loop through it
    'slides': slides
})




def update_adminindex(request, pk):
    admin_data = get_object_or_404(AdminIndex, pk=pk)

    if request.method == 'POST':
        # Update logic
        admin_data.num_institutions = request.POST.get('partners', admin_data.num_institutions)
        admin_data.num_trainees = request.POST.get('trainees', admin_data.num_trainees)
        admin_data.num_trainers = request.POST.get('trainers', admin_data.num_trainers)
        admin_data.save()
        return redirect('admin_index')

    return render(request, 'adminpages/update_adminindex.html', {'admin_data': admin_data})


def delete_slide(request, slide_id):
    if request.method == 'POST':
        slide = get_object_or_404(CarouselSlide, id=slide_id)
        slide.delete()
    return redirect('admin_index')



def about(request):
    about_data = AdminAbout.objects.first()
    return render(request, 'clientside/about.html', {'about_data': about_data})


def admin_about(request):
    # Get or create the primary AdminAbout instance (used for the form)
    about_data, created = AdminAbout.objects.get_or_create(pk=1)

    if request.method == 'POST':
        about_data.title = request.POST.get('title')
        about_data.paragraph1 = request.POST.get('paragraph1')
        about_data.paragraph2 = request.POST.get('paragraph2')
        about_data.paragraph3 = request.POST.get('paragraph3')
        about_data.phone = request.POST.get('phone')

        if 'image' in request.FILES:
            about_data.image = request.FILES['image']

        about_data.save()
        return redirect('admin_about')

    # Pass both the form instance and all AdminAbout records for the table
    all_about_entries = AdminAbout.objects.all()

    return render(request, 'adminpages/admin_about.html', {
        'about': about_data,
        'adminabout_items': all_about_entries
    })

def update_admin_about(request, pk):
    about = get_object_or_404(AdminAbout, pk=pk)

    if request.method == 'POST':
        about.title = request.POST.get('title')
        about.paragraph1 = request.POST.get('paragraph1')
        about.paragraph2 = request.POST.get('paragraph2')
        about.paragraph3 = request.POST.get('paragraph3')
        about.phone = request.POST.get('phone')

        if 'image' in request.FILES:
            about.image = request.FILES['image']

        about.save()
        return redirect('admin_about')

    return render(request, 'adminpages/update_admin_about.html', {'about': about})



def admin_inst_mgt(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        title = request.POST.get('title')
        twitter = request.POST.get('twitter')
        facebook = request.POST.get('facebook')
        linkedin = request.POST.get('linkedin')
        image = request.FILES.get('image')

        if name and title and image:
            AdminInstitutionalManagement.objects.create(
                name=name,
                title=title,
                twitter=twitter,
                facebook=facebook,
                linkedin=linkedin,
                image=image
            )
            return redirect('admin_inst_mgt')

    managers = AdminInstitutionalManagement.objects.all()
    return render(request, 'adminpages/admin_inst_mgt.html', {'managers': managers})

def update_manager(request, manager_id):
    manager = get_object_or_404(AdminInstitutionalManagement, id=manager_id)

    if request.method == 'POST':
        manager.name = request.POST.get('name')
        manager.title = request.POST.get('title')
        manager.twitter = request.POST.get('twitter')
        manager.facebook = request.POST.get('facebook')
        manager.linkedin = request.POST.get('linkedin')

        if 'image' in request.FILES:
            manager.image = request.FILES['image']

        manager.save()
        return redirect('admin_inst_mgt')

    return render(request, 'adminpages/update_manager.html', {'manager': manager})

def admin_bom(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        title = request.POST.get('title')
        twitter = request.POST.get('twitter')
        facebook = request.POST.get('facebook')
        linkedin = request.POST.get('linkedin')
        image = request.FILES.get('image')

        if name and title and image:
            AdminBom.objects.create(
                name=name,
                title=title,
                twitter=twitter,
                facebook=facebook,
                linkedin=linkedin,
                image=image
            )
            return redirect('admin_bom')

    managers = AdminBom.objects.all()
    return render(request, 'adminpages/admin_bom.html', {'managers': managers})

def admin_academic_departments(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        heading = request.POST.get('heading')
        description = request.POST.get('description')
        read_more_link = request.POST.get('read_more_link')
        image = request.FILES.get('image')

        AdminAcDpt.objects.create(
            name=name,
            heading=heading,
            description=description,
            read_more_link=read_more_link,
            image=image
        )
        return redirect('admin_academic_departments')  # replace with your actual view name

    departments = AdminAcDpt.objects.all()
    return render(request, 'adminpages/admin_acdpts.html', {'departments': departments})

def admin_non_academic_departments(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        heading = request.POST.get('heading')
        description = request.POST.get('description')
        read_more_link = request.POST.get('read_more_link')
        image = request.FILES.get('image')

        AdminNonAcDpt.objects.create(
            name=name,
            heading=heading,
            description=description,
            read_more_link=read_more_link,
            image=image
        )
        return redirect('admin_non_academic_departments')  # replace with your actual view name

    departments = AdminNonAcDpt.objects.all()
    return render(request, 'adminpages/admin_non_acdpts.html', {'departments': departments})

def admin_dashboard(request):
    return render(request, 'adminpages/admin_dashboard.html')


@csrf_protect
def trainee_registration(request):
    if request.method == 'POST':
        admission_date_str = request.POST.get('date_of_admission')
        try:
            admission_date = datetime.strptime(admission_date_str, '%Y-%m-%d').date()
        except ValueError:
            admission_date = None

        passport_image = request.FILES.get('passport_image')  # ✅ handle image file

        trainee = Trainee.objects.create(
            first_name=request.POST.get('first_name'),
            middle_name=request.POST.get('middle_name'),
            last_name=request.POST.get('last_name'),
            gender=request.POST.get('gender'),
            age=request.POST.get('age'),
            date_of_admission=admission_date,
            course=Course.objects.get(id=request.POST.get('course')),
            department=Department.objects.get(id=request.POST.get('department')),
            
            kcse_index=request.POST.get('kcse_index'),
            kcse_grade=request.POST.get('kcse_grade'),
            kcse_year=request.POST.get('kcse_year'),
            kcpe_index=request.POST.get('kcpe_index'),
            kcpe_grade=request.POST.get('kcpe_grade'),
            kcpe_year=request.POST.get('kcpe_year'),
            county=request.POST.get('county'),
            sub_county=request.POST.get('sub_county'),
            division=request.POST.get('division'),
            location=request.POST.get('location'),
            phone=request.POST.get('phone'),
            id_number=request.POST.get('id_number'),
            email=request.POST.get('email'),
            guardian_name=request.POST.get('guardian_name'),
            guardian_phone=request.POST.get('guardian_phone'),
            guardian_id=request.POST.get('guardian_id'),
            passport_image=passport_image if passport_image else None  # ✅ optional
        )

        messages.success(request, "Trainee registered successfully!")
        return redirect('trainee_profile', trainee_id=trainee.id)

    departments = Department.objects.all()
    
    return render(request, 'registrar_academics/trainee_reg.html', {
        'departments': departments,
        
    })


def registrar_register_session(request):
    warning = None
    errors = []

    if request.method == 'POST':
        trainee_number = request.POST.get('trainee_number')

        try:
            trainee = Trainee.objects.get(trainee_number=trainee_number)

            try:
                current_session = CurrentSession.objects.get(is_active=True)
            except CurrentSession.DoesNotExist:
                errors.append("No active session available.")
                current_session = None

            if current_session:
                if TraineeSession.objects.filter(
                    trainee=trainee,
                    session_period=current_session.session_period
                ).exists():
                    warning = f"{trainee} is already registered for {current_session.session_period}."
                else:
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

                    session = TraineeSession(
                        trainee=trainee,
                        current_session=current_session,
                        session_period=current_session.session_period,
                        year_of_study=year_of_study,
                        term=term,
                    )
                    try:
                        session.save()

                        # ✅ Create FeeStatement DEBIT entry
                        debit_payment_id = f"INV-DEBIT-{session.id}"
                        FeeStatement.objects.create(
                            trainee=trainee,
                            transaction_type="DEBIT",
                            amount=session.fee_balance,   # total charge (including carry forward)
                            balance_after=session.fee_balance,
                            invoice_number=debit_payment_id,
                            reference=debit_payment_id,
                            session_period=session.session_period,
                            year_of_study=session.year_of_study,   # ✅ store year
                            term=session.term                      # ✅ store term
                        )

                        warning = f"{trainee} successfully registered for {current_session.session_period} (Year {year_of_study} Term {term})."
                    except ValidationError as ve:
                        for field, messages in ve.message_dict.items():
                            errors.extend(messages)

        except Trainee.DoesNotExist:
            errors.append("Trainee not found.")

    return render(request, 'registrar_academics/register_session.html', {
        'warning': warning,
        'errors': errors
    })




def create_current_session(request):
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        try:
            # Convert strings to date objects
            from datetime import datetime
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()

            # Expire all old sessions
            CurrentSession.objects.filter(end_date__lt=timezone.now().date()).update(is_active=False)

            # Create new current session
            current_session = CurrentSession(start_date=start_date_obj, end_date=end_date_obj)
            current_session.full_clean()  # run model validations
            current_session.save()
            messages.success(request, "Current session created successfully.")
            return redirect('create_current_session')

        except Exception as e:
            messages.error(request, f"Error creating session: {e}")

    return render(request, 'registrar_academics/create_current_session.html')



def trainees_in_session(request):
    # Get the active current session based on today's date
    today = timezone.now().date()
    current_session = CurrentSession.objects.filter(
        start_date__lte=today,
        end_date__gte=today,
        is_active=True
    ).first()

    trainees = []
    if current_session:
        # Fetch all TraineeSession records registered within the current session
        trainees = TraineeSession.objects.filter(
            date_registered__range=(current_session.start_date, current_session.end_date)
        ).select_related('trainee', 'trainee__course')

    context = {
        'current_session': current_session,
        'trainees': trainees
    }
    return render(request, 'registrar_academics/trainees_in_session.html', context)





def edit_trainee(request, trainee_id):
    trainee = get_object_or_404(Trainee, id=trainee_id)

    if request.method == 'POST':
        admission_date_str = request.POST.get('date_of_admission')
        try:
            admission_date = datetime.strptime(admission_date_str, '%Y-%m-%d').date()
        except ValueError:
            admission_date = None

        # Extract number part from existing trainee_number
        match = re.search(r'/(\d{4})/', trainee.trainee_number)
        number_part = match.group(1) if match else None

        # Update fields
        trainee.first_name = request.POST.get('first_name')
        trainee.middle_name = request.POST.get('middle_name')
        trainee.last_name = request.POST.get('last_name')
        trainee.gender = request.POST.get('gender')
        trainee.age = request.POST.get('age')
        trainee.date_of_admission = admission_date
        trainee.course = Course.objects.get(id=request.POST.get('course'))
        trainee.department = Department.objects.get(id=request.POST.get('department'))
        trainee.level = request.POST.get('level')
        trainee.kcse_index = request.POST.get('kcse_index')
        trainee.kcse_grade = request.POST.get('kcse_grade')
        trainee.kcse_year = request.POST.get('kcse_year')
        trainee.kcpe_index = request.POST.get('kcpe_index')
        trainee.kcpe_grade = request.POST.get('kcpe_grade')
        trainee.kcpe_year = request.POST.get('kcpe_year')
        trainee.county = request.POST.get('county')
        trainee.sub_county = request.POST.get('sub_county')
        trainee.division = request.POST.get('division')
        trainee.location = request.POST.get('location')
        trainee.phone = request.POST.get('phone')
        trainee.id_number = request.POST.get('id_number')
        trainee.email = request.POST.get('email')
        trainee.guardian_name = request.POST.get('guardian_name')
        trainee.guardian_phone = request.POST.get('guardian_phone')
        trainee.guardian_id = request.POST.get('guardian_id')

        # ✅ Handle passport photo update
        if request.FILES.get('passport_image'):
            trainee.passport_image = request.FILES['passport_image']

        # Regenerate trainee number with old count
        trainee.trainee_number = trainee.generate_trainee_number(number_part)
        trainee.save()

        messages.success(request, "Trainee profile updated successfully!")
        return redirect('trainee_profile', trainee_id=trainee.id)

    departments = Department.objects.all()
    return render(request, 'registrar_academics/edit_trainee_profile.html', {
        'trainee': trainee,
        'departments': departments,
    })



def get_courses(request, dept_id):
    courses = Course.objects.filter(department_id=dept_id).values('id', 'name')
    return JsonResponse(list(courses), safe=False)

def trainee_profile(request, trainee_id):
    trainee = get_object_or_404(Trainee, id=trainee_id)
    return render(request, 'registrar_academics/trainees_profile.html', {'trainee': trainee})


def all_trainees(request):
    trainees = Trainee.objects.all()
    return render(request, 'registrar_academics/all_trainees.html', {'trainees': trainees})



def admin_logout(request):
    # Clear all session data
    request.session.flush()
    
    # Redirect to the login page
    return redirect('admin_login')


def registrar_academics_dashboard(request):
    if request.session.get('designation') != 'Registrar Academics':
        return redirect('admin_login')

    
    return render(request, 'registrar_academics/registrar_academics_dashboard.html')


def dp_admin_dashboard(request):
    designation = request.session.get('designation', '').strip().lower()
    if designation != 'dp admin':
        return redirect('admin_login')
    return render(request, 'dp_admin/dp_admin_dashboard.html')



def dp_academics_dashboard(request):
    designation = request.session.get('designation', '').strip().lower()
    if designation != 'dp academics':
        return redirect('admin_login')
    return render(request, 'dp_academics/dp_academics_dashboard.html')


# def hod_dashboard_view(request):
#     if request.session.get('designation') != 'HOD':
#         return redirect('admin_login')
#     return render(request, 'dashboard/hod.html', {'name': request.session.get('admin_name')})

# def dp_academics_dashboard_view(request):
#     if request.session.get('designation') != 'DP Academics':
#         return redirect('admin_login')
#     return render(request, 'dashboard/dp_academics.html', {'name': request.session.get('admin_name')})


import re

def gender_by_intake_data(request):
    trainees = Trainee.objects.exclude(trainee_number='').exclude(gender__isnull=True)

    # Extract intake codes and group by gender
    intakes = {}
    for s in trainees:
        match = re.search(r'(\d{2}[A-Z])$', s.trainee_number)  # Matches like 23J, 23M, 23S
        if match:
            code = match.group(1)
            if code not in intakes:
                intakes[code] = {"Male": 0, "Female": 0}
            if s.gender == 'Male':
                intakes[code]["Male"] += 1
            elif s.gender == 'Female':
                intakes[code]["Female"] += 1

    # Sort intake codes chronologically
    sorted_codes = sorted(intakes.keys())
    
    labels = sorted_codes
    male_data = [intakes[code]["Male"] for code in sorted_codes]
    female_data = [intakes[code]["Female"] for code in sorted_codes]

    chart_data = {
        "labels": labels,
        "datasets": [
            {
                "label": "Male Trainees",
                "fillColor": "rgba(60,141,188,0.9)",
                "strokeColor": "rgba(60,141,188,0.8)",
                "pointColor": "#3b8bba",
                "pointStrokeColor": "rgba(60,141,188,1)",
                "pointHighlightFill": "#fff",
                "pointHighlightStroke": "rgba(60,141,188,1)",
                "data": male_data
            },
            {
                "label": "Female Trainees",
                "fillColor": "rgba(210,214,222,0.9)",
                "strokeColor": "rgba(210,214,222,0.8)",
                "pointColor": "#c1c7d1",
                "pointStrokeColor": "rgba(210,214,222,1)",
                "pointHighlightFill": "#fff",
                "pointHighlightStroke": "rgba(220,220,220,1)",
                "data": female_data
            }
        ]
    }

    return JsonResponse(chart_data)

def department_trainee_data(request):
    department_counts = Trainee.objects.values('department__name').annotate(count=Count('id'))

    colors = [
        "#f56954", "#00a65a", "#f39c12", "#00c0ef",
        "#3c8dbc", "#d2d6de", "#8e44ad", "#27ae60"
    ]

    data = []
    for index, entry in enumerate(department_counts):
        data.append({
            'label': entry['department__name'] or 'Unassigned',
            'value': entry['count'],
            'color': colors[index % len(colors)],
            'highlight': colors[index % len(colors)]
        })

    return JsonResponse(data, safe=False)

def trainee_progress_stats_api(request):
    total_male = Trainee.objects.filter(gender='Male').count()
    total_female = Trainee.objects.filter(gender='Female').count()
    total_all = Trainee.objects.count()

    # Get latest intake by date
    latest_date = Trainee.objects.order_by('-date_of_admission').values_list('date_of_admission', flat=True).first()

    latest_male = latest_female = latest_total = 0
    if latest_date:
        latest_year = latest_date.year
        latest_month = latest_date.month
        latest_intake = Trainee.objects.filter(date_of_admission__year=latest_year, date_of_admission__month=latest_month)
        latest_male = latest_intake.filter(gender='Male').count()
        latest_female = latest_intake.filter(gender='Female').count()
        latest_total = latest_intake.count()

    return JsonResponse({
        "total_male": total_male,
        "total_female": total_female,
        "total_all": total_all,
        "latest_male": latest_male,
        "latest_female": latest_female,
        "latest_total": latest_total,
    })



def top_courses_api(request):
    # Group trainees by course and intake code
    trainee_data = Trainee.objects.all().select_related('course')

    course_intake_counts = defaultdict(lambda: defaultdict(int))  # {course_name: {intake: count}}

    for trainee in trainee_data:
        course_name = trainee.course.name
        intake_code = trainee.trainee_number.split('/')[-1]  # Extract intake code from trainee number
        course_intake_counts[course_name][intake_code] += 1

    response_data = []

    for course_name, intakes in course_intake_counts.items():
        sorted_intakes = sorted(intakes.items())  # Sort by intake code
        if len(sorted_intakes) >= 2:
            prev_intake, prev_count = sorted_intakes[-2]
            curr_intake, curr_count = sorted_intakes[-1]
            try:
                percent_change = round(((curr_count - prev_count) / prev_count) * 100, 1)
            except ZeroDivisionError:
                percent_change = 100.0  # If previous is 0, we assume full increase
        else:
            curr_intake, curr_count = sorted_intakes[-1]
            percent_change = 0.0  # No comparison available

        response_data.append({
            'name': course_name,
            'current': curr_count,
            'percent_change': percent_change,
        })

    # Optional: Sort by highest current intake
    response_data.sort(key=lambda x: x['current'], reverse=True)

    return JsonResponse(response_data, safe=False)

from django.http import JsonResponse
from .models import Trainee  # adjust the import if your model is named differently

from django.core.serializers import serialize
from django.utils.timesince import timesince



def api_recent_trainees(request):
    trainees = Trainee.objects.order_by('-date_of_admission')[:12]
    data = []

    for trainee in trainees:
        data.append({
            'id': trainee.id,  # 🔁 Add this line
            'name': trainee.first_name,
            'image_url': trainee.passport_image.url if trainee.passport_image else '/static/img/default.jpg',
            'date_label': timesince(trainee.date_of_admission).split(',')[0] + ' ago'
        })

    return JsonResponse(data, safe=False)

def recent_courses_api(request):
    courses = Course.objects.select_related('department').order_by('-id')[:4]
    data = []

    for course in courses:
        data.append({
            'name': course.name,
            'department': course.department.name,
            'price': "Ksh 0",  # Optional placeholder
            'description': f"Department: {course.department.name}",
            'image': '/static/img/default-50x50.gif',
        })

    return JsonResponse(data, safe=False)

def total_trainees_api(request):
    total = Trainee.objects.count()
    return JsonResponse({'total_trainees': total})





def total_trainees_in_session(request):
    # Get the current active session
    current_session = CurrentSession.objects.filter(
        start_date__lte=timezone.now().date(),
        end_date__gte=timezone.now().date(),
        is_active=True
    ).first()

    if not current_session:
        return JsonResponse({"total_trainees": 0, "message": "No active session found."})

    # Count all trainees registered within this session period
    total_trainees = TraineeSession.objects.filter(
        date_registered__gte=current_session.start_date,
        date_registered__lte=current_session.end_date
    ).count()

    return JsonResponse({"total_trainees": total_trainees})


def gender_intake_stats_api(request):
    data = {}

    # 1. Total males and females
    total_males = Trainee.objects.filter(gender='Male').count()
    total_females = Trainee.objects.filter(gender='Female').count()

    data['total_males'] = total_males
    data['total_females'] = total_females

    # 2. Extract intake codes from trainee_number and group by gender
    trainees = Trainee.objects.exclude(trainee_number='').exclude(gender__isnull=True)
    
    intakes = {}
    for s in trainees:
        match = re.search(r'(\d{2}[A-Z])$', s.trainee_number)  # Matches like 23J, 24M, etc.
        if match:
            code = match.group(1)
            if code not in intakes:
                intakes[code] = {'Male': 0, 'Female': 0}
            if s.gender == 'Male':
                intakes[code]['Male'] += 1
            elif s.gender == 'Female':
                intakes[code]['Female'] += 1

    # Sort intake codes (latest first)
    sorted_intakes = sorted(intakes.keys(), reverse=True)

    # Ensure at least 2 intakes to compare
    if len(sorted_intakes) >= 2:
        latest = sorted_intakes[0]
        previous = sorted_intakes[1]

        male_latest = intakes[latest]['Male']
        female_latest = intakes[latest]['Female']

        male_previous = intakes[previous]['Male']
        female_previous = intakes[previous]['Female']

        # Calculate % change
        def percent_change(current, previous):
            if previous == 0:
                return 100 if current > 0 else 0
            return round(((current - previous) / previous) * 100)

        data.update({
            'latest_intake': latest,
            'previous_intake': previous,
            'male_latest': male_latest,
            'female_latest': female_latest,
            'male_latest_pct': percent_change(male_latest, male_previous),
            'female_latest_pct': percent_change(female_latest, female_previous),
        })
    else:
        data['error'] = "Not enough valid intakes to compare."

    return JsonResponse(data)

def all_departments(request):
    departments = Department.objects.all()
    departments_data = []

    for dept in departments:
        courses = Course.objects.filter(department=dept)
        total_courses = courses.count()

        trainees = Trainee.objects.filter(course__in=courses).order_by('-date_of_admission')
        total_trainees = trainees.count()

        intakes_by_month = (
            trainees
            .dates('date_of_admission', 'month', order='DESC')[:2]
        )

        latest_intake = 0
        previous_intake = 0
        percentage_change = "N/A"

        if intakes_by_month:
            latest_month = intakes_by_month[0]
            latest_intake = trainees.filter(
                date_of_admission__month=latest_month.month,
                date_of_admission__year=latest_month.year
            ).count()

        if len(intakes_by_month) > 1:
            previous_month = intakes_by_month[1]
            previous_intake = trainees.filter(
                date_of_admission__month=previous_month.month,
                date_of_admission__year=previous_month.year
            ).count()

            if previous_intake > 0:
                change = ((latest_intake - previous_intake) / previous_intake) * 100
                percentage_change = f"{change:.1f}%"
            else:
                percentage_change = "∞"

        departments_data.append({
            'department_name': dept.name,
            'total_courses': total_courses,
            'total_trainees': total_trainees,
            'latest_intake': latest_intake,
            'percentage_change': percentage_change,
            'trainers': "N/A",  # Update later when Trainer model exists
            'overview': getattr(dept, 'description', "N/A")
        })

    return render(request, 'registrar_academics/all_departments.html', {'departments_data': departments_data})

def all_departments_dpac(request):
    departments = Department.objects.all()
    departments_data = []

    for dept in departments:
        courses = Course.objects.filter(department=dept)
        total_courses = courses.count()

        trainees = Trainee.objects.filter(course__in=courses).order_by('-date_of_admission')
        total_trainees = trainees.count()

        intakes_by_month = (
            trainees
            .dates('date_of_admission', 'month', order='DESC')[:2]
        )

        latest_intake = 0
        previous_intake = 0
        percentage_change = "N/A"

        if intakes_by_month:
            latest_month = intakes_by_month[0]
            latest_intake = trainees.filter(
                date_of_admission__month=latest_month.month,
                date_of_admission__year=latest_month.year
            ).count()

        if len(intakes_by_month) > 1:
            previous_month = intakes_by_month[1]
            previous_intake = trainees.filter(
                date_of_admission__month=previous_month.month,
                date_of_admission__year=previous_month.year
            ).count()

            if previous_intake > 0:
                change = ((latest_intake - previous_intake) / previous_intake) * 100
                percentage_change = f"{change:.1f}%"
            else:
                percentage_change = "∞"

        departments_data.append({
            'department_name': dept.name,
            'total_courses': total_courses,
            'total_trainees': total_trainees,
            'latest_intake': latest_intake,
            'percentage_change': percentage_change,
            'trainers': "N/A",  # Update later when Trainer model exists
            'overview': getattr(dept, 'description', "N/A")
        })

    return render(request, 'dp_academics/all_departments.html', {'departments_data': departments_data})



def all_courses(request):
    courses = Course.objects.select_related('department').all()
    course_data = []

    for course in courses:
        # All trainees in this course
        trainees = Trainee.objects.filter(course=course).order_by('-date_of_admission')
        total_trainees = trainees.count()

        # Group intakes by month
        intakes_by_month = (
            trainees
            .dates('date_of_admission', 'month', order='DESC')[:2]
        )

        latest_intake = 0
        previous_intake = 0
        percentage_change = "N/A"

        if intakes_by_month:
            latest_month = intakes_by_month[0]
            latest_intake = trainees.filter(
                date_of_admission__month=latest_month.month,
                date_of_admission__year=latest_month.year
            ).count()

        if len(intakes_by_month) > 1:
            previous_month = intakes_by_month[1]
            previous_intake = trainees.filter(
                date_of_admission__month=previous_month.month,
                date_of_admission__year=previous_month.year
            ).count()

            if previous_intake > 0:
                change = ((latest_intake - previous_intake) / previous_intake) * 100
                percentage_change = f"{change:.1f}%"
            else:
                percentage_change = "∞"

        course_data.append({
            'name': course.name,
            'department': course.department.name if course.department else "N/A",
            'level': course.level if hasattr(course, 'level') else "N/A",
            'total_trainees': total_trainees,
            'latest_intake': latest_intake,
            'percentage_change': percentage_change,
        })

    return render(request, 'registrar_academics/all_courses.html', {'courses': course_data})

def all_courses_dpac(request):
    courses = Course.objects.select_related('department').all()
    course_data = []

    for course in courses:
        # All trainees in this course
        trainees = Trainee.objects.filter(course=course).order_by('-date_of_admission')
        total_trainees = trainees.count()

        # Group intakes by month
        intakes_by_month = (
            trainees
            .dates('date_of_admission', 'month', order='DESC')[:2]
        )

        latest_intake = 0
        previous_intake = 0
        percentage_change = "N/A"

        if intakes_by_month:
            latest_month = intakes_by_month[0]
            latest_intake = trainees.filter(
                date_of_admission__month=latest_month.month,
                date_of_admission__year=latest_month.year
            ).count()

        if len(intakes_by_month) > 1:
            previous_month = intakes_by_month[1]
            previous_intake = trainees.filter(
                date_of_admission__month=previous_month.month,
                date_of_admission__year=previous_month.year
            ).count()

            if previous_intake > 0:
                change = ((latest_intake - previous_intake) / previous_intake) * 100
                percentage_change = f"{change:.1f}%"
            else:
                percentage_change = "∞"

        course_data.append({
            'name': course.name,
            'department': course.department.name if course.department else "N/A",
            'level': course.level if hasattr(course, 'level') else "N/A",
            'total_trainees': total_trainees,
            'latest_intake': latest_intake,
            'percentage_change': percentage_change,
        })

    return render(request, 'dp_academics/all_courses.html', {'courses': course_data})

def add_department(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        date_registered = request.POST.get('date_registered')

        # fallback to today's date if empty
        if not date_registered:
            date_registered = timezone.now().date()

        # Save the department
        Department.objects.create(
            name=name,
            code=code,
            date_registered=date_registered
        )
        return redirect('all_departments')  # Replace with your list view name

    return render(request, 'dp_academics/add_department.html')

from django.shortcuts import render, redirect
from .models import Course, Department
from decimal import Decimal

def add_course(request):
    if request.method == 'POST':
        name = request.POST.get('course_name')
        code = request.POST.get('course_code')
        level = request.POST.get('level')
        date_registered = request.POST.get('date_registered')
        department_id = request.POST.get('department_id')

        # New: fees inputs
        term1_fees = request.POST.get('term1_fees')
        term2_fees = request.POST.get('term2_fees')
        term3_fees = request.POST.get('term3_fees')

        if name and code and level and date_registered and department_id:
            try:
                department = Department.objects.get(id=department_id)

                # Prepend level to course name (e.g., "L4 Computing and Informatics")
                formatted_name = f"{level.split()[-1]} {name}"  
                formatted_name = f"L{formatted_name}"

                Course.objects.create(
                    name=formatted_name,
                    code=code,
                    level=level,
                    date_registered=date_registered,
                    department=department,
                    term1_fees=Decimal(term1_fees or 0),
                    term2_fees=Decimal(term2_fees or 0),
                    term3_fees=Decimal(term3_fees or 0)
                )
                return redirect('all_courses_dpac')  # Redirect to the courses list

            except Department.DoesNotExist:
                pass

    departments = Department.objects.all()
    return render(request, 'dp_academics/add_course.html', {'departments': departments})

# <<Dp_Academics Views>>
from .models import TrainerData, Department, Course

def dp_academics_dashboard(request):
    designation = request.session.get('designation', '').strip().lower()
    if designation != 'dp academics':
        return redirect('admin_login')
    return render(request, 'dp_academics/dp_academics_dashboard.html')

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Department, Course

def trainer_registration(request):
    departments = Department.objects.all()
    courses = Course.objects.all()  # Used only if you want all courses initially

    if request.method == "POST":
        # Personal Info
        first_name = request.POST.get('first_name')
        middle_name = request.POST.get('middle_name', '')
        last_name = request.POST.get('last_name')
        gender = request.POST.get('gender')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        passport_image = request.FILES.get('passport_image')

        # Department
        department_id = request.POST.get('department')
        department = Department.objects.get(id=department_id) if department_id else None

        # Courses (comma-separated string from hidden input)
        course_ids_str = request.POST.get('courses', '')  # e.g., "1,3,5"
        course_ids = course_ids_str.split(',') if course_ids_str else []
        selected_courses = Course.objects.filter(id__in=course_ids)

        # Qualifications
        highest_education = request.POST.get('highest_education', '')
        certificates = request.POST.get('certificates', '')

        # Residential info
        county = request.POST.get('county', '')
        sub_county = request.POST.get('sub_county', '')
        town = request.POST.get('town', '')

        # Create Trainer
        trainer = TrainerData.objects.create(
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            gender=gender,
            phone=phone,
            email=email,
            passport_image=passport_image,
            department=department,
            highest_education=highest_education,
            certificates=certificates,
            county=county,
            sub_county=sub_county,
            town=town
        )

        # Add Many-to-Many courses
        trainer.courses.set(selected_courses)
        trainer.save()

        messages.success(request, f"Trainer {trainer.first_name} {trainer.last_name} registered successfully!")
        return redirect('trainer_registration')

    context = {
        'departments': departments,
        'courses': courses
    }
    return render(request, 'dp_academics/staff_reg.html', context)
