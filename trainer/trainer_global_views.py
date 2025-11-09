from django.shortcuts import render, redirect

def staff_dashboard(request):
    return render(request, 'trainer/staff_dashboard.html')