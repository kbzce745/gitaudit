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
    milestones = [
        {'name': 'Project Topic & High Level scope', 'status': 'Completed'},
        {'name': 'Requirements / Analysis', 'status': 'On track'},
        {'name': 'Tools, Stack, Dev. Environment', 'status': 'On track'},
        {'name': 'Prototype and Design', 'status': 'Not Started'},
        {'name': 'Development', 'status': 'Not Started'},
        {'name': 'System testing', 'status': 'Not Started'},
        {'name': 'User Evaluations', 'status': 'Not Started'},
        {'name': 'Dissertation & Video', 'status': 'Not Started'},
    ]
    
    current_week = 8
    
    BI_WEEKLY_REPORTS = {
        '3/4': {
            'title': 'Week 3/4 Status Update',
            'intro': 'By your meeting in Week 3/4, you should be able to update your supervisor on:',
            'items': [
                'A <strong>clearly defined project topic</strong>',
                'What <strong>requirements capture, background reading, and literature review</strong> you’ve conducted, and what you’ve found.',
                'Any <strong>additional research into tools, frameworks, APIs</strong> you’ve done that will help you toward design and implementation.'
            ]
        },
        '6/7': {
            'title': 'Week 6/7 Status Update',
            'intro': 'By the Week 6/7 meeting, you should be able to update your supervisor on:',
            'items': [
                'The <strong>final design and aims</strong> of the project',
                'Any <strong>prototyping activities</strong> undertaken',
                'The <strong>current status of your build</strong>, including a live demonstration of your development environment.',
                '<strong>Dissertation progress</strong> (e.g. writing up the introduction, background/requirements and design chapters).'
            ]
        },
        '8/9': {
            'title': 'Week 8/9 Status Update',
            'intro': 'By the Week 8/9 meeting, you should be able to update your supervisor on:',
            'items': [
                'A <strong>demonstration of the current state of your build</strong>, and how close you are to your MVP',
                'Your <strong>plan and remaining objectives</strong> to complete development',
                'Your plan on how you are going <strong>to evaluate that your system is fit-for-purpose</strong>',
                '<strong>Dissertation progress</strong> (e.g. writing up the implementation chapter)'
            ]
        },
        '10/11': {
            'title': 'Week 10/11 Status Update',
            'intro': 'By the Week 10/11 meeting, you should be able to update your supervisor on:',
            'items': [
                'The <strong>results of any evaluations and testing</strong> conducted or in-progress',
                '<strong>Remaining dissertation writing</strong> (e.g. evaluation, discussion, conclusions), and your plan for the last 2 weeks and final write-up.',
                'Any remaining content you would like supervisor feedback on, if they have time.'
            ]
        }
    }
    
    bi_weekly_key = None
    if current_week in [3, 4]:
        bi_weekly_key = '3/4'
    elif current_week in [6, 7]:
        bi_weekly_key = '6/7'
    elif current_week in [8, 9]:
        bi_weekly_key = '8/9'
    elif current_week in [10, 11]:
        bi_weekly_key = '10/11'
        
    bi_weekly_data = BI_WEEKLY_REPORTS.get(bi_weekly_key)
    
    # Dummy context data for the Top Banner
    context = {
        'current_week': current_week,
        'report_status': 'Draft', # Options: Draft, Locked, Reviewed
        'next_meeting_days': 2,
        'milestones': milestones,
        'bi_weekly_data': bi_weekly_data,
    }
    return render(request, 'auditor/student_dashboard.html', context)

@login_required
def teacher_dashboard(request):
    # Temporary placeholder
    return render(request, 'auditor/base.html')
