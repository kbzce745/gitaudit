from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def login_view(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'profile') and request.user.profile.role == 'teacher':
            return redirect('teacher_dashboard')
        return redirect('student_dashboard')

    if request.method == 'POST':
        login_id = request.POST.get('username')
        password = request.POST.get('password')
        
        # Try finding user by email first
        try:
            user_obj = User.objects.get(email=login_id)
            username = user_obj.username
        except User.DoesNotExist:
            username = login_id

        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            auth_login(request, user)
            if hasattr(user, 'profile') and user.profile.role == 'teacher':
                return redirect('teacher_dashboard')
            return redirect('student_dashboard')
        else:
            messages.error(request, 'Invalid email/username or password')
            
    return render(request, 'auditor/login.html')

def logout_view(request):
    auth_logout(request)
    return redirect('login')

@login_required
def student_dashboard(request):
    # Dummy context data for the Top Banner
    context = {
        'current_week': 8,
        'report_status': 'Draft', # Options: Draft, Locked, Reviewed
        'next_meeting_days': 2
    }
    return render(request, 'auditor/student_dashboard.html', context)

@login_required
def teacher_dashboard(request):
    # Temporary placeholder
    return render(request, 'auditor/base.html')
