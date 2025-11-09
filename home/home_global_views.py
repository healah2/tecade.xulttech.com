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
from .models import Trainee, Course
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
# views.py
from django.http import JsonResponse
from .models import Trainee, CurrentSession, TraineeSession


def admin_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        staff_number = request.POST.get('staff_number')

        try:
            admin = AdminCredentials.objects.get(username=username, staff_number=staff_number)
            
            # Save session data
            request.session['admin_id'] = admin.id
            request.session['admin_name'] = admin.name
            request.session['designation'] = admin.designation

            # Save profile image path (or fallback)
            request.session['profile_image_url'] = (
                admin.profile_image.url if admin.profile_image else '/static/dist/img/user2-160x160.jpg'
            )

            # Normalize and route by designation
            designation = admin.designation.strip().lower()

            if designation == 'registrar academics':
                return redirect('registrar_academics_dashboard')
            elif designation == 'hod':
                return redirect('hod_dashboard')
            elif designation == 'dp academics':
                return redirect('dp_academics_dashboard')
            elif designation == 'dp admin':
                return redirect('dp_admin_dashboard')
            elif designation == 'finance':
                return redirect('finance_dashboard')
            else:
                messages.error(request, 'Dashboard for this designation is not yet configured.')
        except AdminCredentials.DoesNotExist:
            messages.error(request, 'Invalid username or staff number.')

    return render(request, 'logins/admin_login.html')

def get_courses(request, dept_id):
    courses = Course.objects.filter(department_id=dept_id).values('id', 'name')
    return JsonResponse(list(courses), safe=False)



from django.views.decorators.http import require_GET

@require_GET
def get_trainee_info(request):
    trainee_number = request.GET.get('trainee_number', '').strip()

    if not trainee_number:
        return JsonResponse({'error': 'Trainee number is required.'})

    try:
        trainee = Trainee.objects.get(trainee_number=trainee_number)
    except Trainee.DoesNotExist:
        return JsonResponse({'error': 'Trainee not registered in current session.'})

    try:
        current_session = CurrentSession.objects.get(is_active=True)
    except CurrentSession.DoesNotExist:
        return JsonResponse({'error': 'No active session currently.'})

    # Check if trainee is enrolled in current session
    try:
        trainee_session = TraineeSession.objects.get(
            trainee=trainee,
            current_session=current_session
        )
        data = {
            'name': f"{trainee.first_name} {trainee.last_name}",
            'session': f"Year: {trainee_session.get_year_of_study_display()}, Term: {trainee_session.get_term_display()}",
            'balance': float(trainee_session.fee_balance)
        }
    except TraineeSession.DoesNotExist:
        data = {'error': 'Trainee is not enrolled in the current active session.'}

    return JsonResponse(data)
