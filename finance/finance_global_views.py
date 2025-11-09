from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect

from django.shortcuts import render
from home import home_global_views


def finance_dashboard(request):
    designation = request.session.get('designation', '').strip().lower()
    if designation != 'finance':
        return redirect('admin_login')
    return render(request, 'finance/finance_dashboard.html')

