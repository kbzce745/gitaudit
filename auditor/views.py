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
    
    # For testing Week 1-4 Project Initiation phase
    current_week = 3
    
    report_status = 'Draft' 

    # Dynamic Bi-Weekly Status Logic based on current_week
    # Mapping based on the exact requirements provided
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
    if current_week <= 4:
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
        'next_meeting_date': '2026-10-24',
        'next_meeting_days': 12,
        'milestones': milestones,
        'bi_weekly_data': bi_weekly_data,
    }
    return render(request, 'auditor/student_dashboard.html', context)

@login_required
def teacher_dashboard(request):
    # Dummy data for the student roster
    students = [
        {
            'id': 1,
            'name': 'Alice Smith',
            'avatar': 'https://ui-avatars.com/api/?name=Alice+Smith&background=003865&color=fff',
            'project_title': 'AI-driven Malware Detection',
            'status': 'Locked', # Pending review
            'last_updated': '2 hours ago',
            'current_week': 6
        },
        {
            'id': 2,
            'name': 'Bob Jones',
            'avatar': 'https://ui-avatars.com/api/?name=Bob+Jones&background=F3D54E&color=0f172a',
            'project_title': 'Blockchain Voting System',
            'status': 'Draft',
            'last_updated': '1 day ago',
            'current_week': 6
        },
        {
            'id': 3,
            'name': 'Charlie Davis',
            'avatar': 'https://ui-avatars.com/api/?name=Charlie+Davis&background=10b981&color=fff',
            'project_title': 'IoT Smart Home Security',
            'status': 'Reviewed',
            'last_updated': '3 days ago',
            'current_week': 6
        }
    ]
    
    # Sort so 'Locked' (Pending Review) students are at the top
    status_priority = {'Locked': 1, 'Draft': 2, 'Reviewed': 3}
    students.sort(key=lambda x: status_priority.get(x['status'], 99))
    
    context = {
        'students': students
    }
    return render(request, 'auditor/teacher_dashboard.html', context)

@login_required
def teacher_student_review(request, student_id):
    if request.method == 'POST':
        # Simulate saving the manual status override to the database
        import json
        from django.http import JsonResponse
        try:
            data = json.loads(request.body)
            day = data.get('day')
            new_status = data.get('status')
            # Here we would update the database record for this student and day
            print(f"Database Updated: Student {student_id}, Day {day}, New Status: {new_status}")
            return JsonResponse({'success': True, 'message': 'Status successfully updated in database.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    # Mock data for the student
    student_info = {
        'id': student_id,
        'name': 'Alice Smith',
        'avatar': 'https://ui-avatars.com/api/?name=Alice+Smith&background=003865&color=fff',
        'project_title': 'AI-driven Malware Detection',
        'current_week': 6,
        'report_status': 'Locked',
    }

    # Re-use the bi-weekly data structure for the left panel
    bi_weekly_data = {
        'title': 'Week 6/7 Status Update',
        'intro': 'By the Week 6/7 meeting, you should be able to update your supervisor on:',
        'items': [
            'The <strong>final design and aims</strong> of the project',
            'Any <strong>prototyping activities</strong> undertaken',
            'The <strong>current status of your build</strong>, including a live demonstration of your development environment.',
            '<strong>Dissertation progress</strong>.'
        ]
    }

    # Daily Audit Logs (Mon-Fri) for the right panel
    daily_audits = [
        {
            'day': 'Monday',
            'date': '2026-10-19',
            'ai_status': 'green',
            'llm_summary': 'Normal progression. Commits align perfectly with the "Database Integration" task claimed in the checklist.',
            'diff_snippet': '+ class User(models.Model):\n+     email = models.EmailField(unique=True)\n+     is_active = models.BooleanField(default=True)\n- # TODO: Add user model'
        },
        {
            'day': 'Tuesday',
            'date': '2026-10-20',
            'ai_status': 'yellow',
            'llm_summary': 'Low commit volume compared to the hours logged. Most changes were just formatting and comment updates.',
            'diff_snippet': '- def process_data(data): # old comment\n+ def process_data(data): # processes raw input'
        },
        {
            'day': 'Wednesday',
            'date': '2026-10-21',
            'ai_status': 'red',
            'llm_summary': 'High risk of copypasta. A huge block of uncredited code was pasted into the utils file in a single commit, matching external libraries.',
            'diff_snippet': '+ def _complex_crypto_hash(val):\n+     # 250 lines of complex hashing logic pasted at once\n+     h = hashlib.sha256()\n+     h.update(val.encode("utf-8"))\n+     h.update(b"salt")\n+     for i in range(1000):\n+         h.update(str(i).encode("utf-8"))\n+         if i % 100 == 0:\n+             print("hashing...", i)\n+     # More fake lines to ensure scrolling\n+     h.update(b"extra padding")\n+     h.update(b"extra padding")\n+     h.update(b"extra padding")\n+     h.update(b"extra padding")\n+     h.update(b"extra padding")\n+     h.update(b"extra padding")\n+     h.update(b"extra padding")\n+     h.update(b"extra padding")\n+     h.update(b"extra padding")\n+     h.update(b"extra padding")\n+     return h.hexdigest()'
        },
        {
            'day': 'Thursday',
            'date': '2026-10-22',
            'ai_status': 'green',
            'llm_summary': 'Solid unit tests added. Test coverage increased by 15%.',
            'diff_snippet': '+ def test_user_creation():\n+     user = User.objects.create(email="test@test.com")\n+     assert user.is_active == True'
        },
        {
            'day': 'Friday',
            'date': '2026-10-23',
            'ai_status': 'green',
            'llm_summary': 'Minor bug fixes and UI styling adjustments using Tailwind.',
            'diff_snippet': '- <div class="bg-red-500">\n+ <div class="bg-red-600 rounded-lg shadow-sm">'
        }
    ]

    context = {
        'student': student_info,
        'bi_weekly_data': bi_weekly_data,
        'daily_audits': daily_audits,
    }
    return render(request, 'auditor/teacher_student_review.html', context)
