from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta, datetime
import json
from django.http import JsonResponse
from .models import BiWeeklyReport, DailyGitAudit, EvidenceImage
from .services import fetch_weekly_diffs, analyze_diff_with_ollama

def login_view(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'profile') and request.user.profile.role == 'teacher':
            return redirect('teacher_dashboard')
        return redirect('student_dashboard')

    if request.method == 'POST':
        login_id = request.POST.get('username')
        password = request.POST.get('password')
        
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
    # Fetch the latest report for this student
    report = BiWeeklyReport.objects.filter(student=request.user).order_by('-created_at').first()
    
    # If no report exists, or the latest one is fully reviewed, start a new draft
    if not report or report.status == 'Reviewed':
        report = BiWeeklyReport.objects.create(
            student=request.user, 
            status='Draft',
            title='Week 8 Status Update'
        )

    if request.method == 'POST':
        if report.status in ['Locked', 'Reviewed']:
            messages.error(request, 'This report is locked and cannot be modified.')
            return redirect('student_dashboard')
            
        action = request.POST.get('action', '')
        
        # Handle Image Deletion
        if action.startswith('delete_image_'):
            image_id = action.replace('delete_image_', '')
            try:
                img = EvidenceImage.objects.get(id=image_id, report=report)
                img.delete()
                messages.success(request, 'Image deleted successfully.')
            except EvidenceImage.DoesNotExist:
                messages.error(request, 'Image not found or already deleted.')
            return redirect('student_dashboard')
            
        # Regardless of action, save the text areas
        report.text_design = request.POST.get('design', report.text_design)
        report.text_prototype = request.POST.get('prototype', report.text_prototype)
        report.text_dissertation = request.POST.get('dissertation', report.text_dissertation)
        report.text_agenda = request.POST.get('agenda', report.text_agenda)
        report.save()
        # Save milestones if sent from frontend
        milestones_json = request.POST.get('milestones_json')
        if milestones_json:
            try:
                report.milestones = json.loads(milestones_json)
            except:
                pass
                
        # Handle images
        for img in request.FILES.getlist('images'):
            EvidenceImage.objects.create(report=report, image=img)
            
        if action == 'generate_audit':
            # Delete old audits for this report to refresh
            DailyGitAudit.objects.filter(report=report).delete()
            
            # Fetch Week 8 explicitly (Aug 10 - Aug 16)
            start_date = datetime(2026, 8, 10).date()
            end_date = datetime(2026, 8, 16).date()
            diff_data = fetch_weekly_diffs(request.user, start_date, end_date)
            
            # Process each day and run through Ollama
            if diff_data:
                for date_str, data in diff_data.items():
                    analysis = analyze_diff_with_ollama(
                        data['raw_diff'],
                        loc_added=data['loc_added'],
                        loc_deleted=data['loc_deleted'],
                        commits_count=data['commits_count']
                    )
                    DailyGitAudit.objects.create(
                        report=report,
                        date=date_str,
                        day_of_week=datetime.strptime(date_str, "%Y-%m-%d").strftime('%A'),
                        raw_diff=data['raw_diff'],
                        loc_added=data['loc_added'],
                        loc_deleted=data['loc_deleted'],
                        llm_summary=analysis['llm_summary'],
                        diff_snippet=analysis['diff_snippet'],
                        ai_status=analysis['ai_status']
                    )
            report.save()
            messages.success(request, 'Audit generated successfully from your recent commits!')
            
        elif action == 'freeze_and_submit':
            report.status = 'Locked'
            report.save()
            messages.success(request, 'Report submitted and locked successfully!')
        else:
            report.save()
            messages.success(request, 'Draft saved.')
            
        return redirect('student_dashboard')

    # Default fallback milestones if none exist
    if not report.milestones:
        report.milestones = [
            {'name': 'Project Topic & High Level scope', 'status': 'Completed'},
            {'name': 'Requirements / Analysis', 'status': 'On track'},
            {'name': 'Tools, Stack, Dev. Environment', 'status': 'On track'},
            {'name': 'Prototype and Design', 'status': 'Not Started'},
            {'name': 'Development', 'status': 'Not Started'},
            {'name': 'System testing', 'status': 'Not Started'},
            {'name': 'User Evaluations', 'status': 'Not Started'},
            {'name': 'Dissertation & Video', 'status': 'Not Started'},
        ]
        report.save()

    # Dynamic Bi-Weekly Status Logic
    bi_weekly_data = {
        'title': report.title,
        'intro': f'By your next meeting, you should be able to update your supervisor on:',
        'items': [
            'The <strong>final design and aims</strong> of the project',
            'Any <strong>prototyping activities</strong> undertaken',
            'The <strong>current status of your build</strong>, including a live demonstration.',
            '<strong>Dissertation progress</strong>.'
        ]
    }
    
    context = {
        'report': report,
        'current_week': 8,
        'report_status': report.status,
        'next_meeting_date': report.meeting_date or '2026-10-24',
        'next_meeting_days': 12,
        'milestones': report.milestones,
        'bi_weekly_data': bi_weekly_data,
    }
    return render(request, 'auditor/student_dashboard.html', context)

@login_required
def teacher_dashboard(request):
    # Fetch real students assigned to this teacher
    teacher = request.user
    students = User.objects.filter(profile__supervisor=teacher)
    
    student_data_list = []
    action_required_count = 0
    for st in students:
        latest_report = st.bi_weekly_reports.order_by('-created_at').first()
        status = latest_report.status if latest_report else 'Draft'
        
        if status == 'Locked':
            action_required_count += 1
            
        repo = st.repositories.first()
        project_title = repo.name if repo else 'CS Project'
        
        student_data_list.append({
            'id': st.id,
            'name': st.get_full_name() or st.username,
            'avatar': f'https://ui-avatars.com/api/?name={st.username}&background=random&color=fff',
            'project_title': project_title,
            'status': status,
            'last_updated': latest_report.updated_at.strftime('%Y-%m-%d %H:%M') if latest_report else 'Never',
            'current_week': 8,
            'report_id': latest_report.id if latest_report else None
        })
        
    # Sort so 'Locked' (Pending Review) students are at the top
    status_priority = {'Locked': 1, 'Draft': 2, 'Changes Requested': 3, 'Reviewed': 4}
    student_data_list.sort(key=lambda x: status_priority.get(x['status'], 99))
    
    context = {
        'students': student_data_list,
        'action_required_count': action_required_count
    }
    return render(request, 'auditor/teacher_dashboard.html', context)

@login_required
def teacher_student_review(request, student_id):
    student = get_object_or_404(User, id=student_id)
    report = BiWeeklyReport.objects.filter(student=student, status='Locked').order_by('-created_at').first()
    
    # If no locked report, try to find the latest one anyway
    if not report:
        report = BiWeeklyReport.objects.filter(student=student).order_by('-created_at').first()
        
    if not report:
        messages.error(request, 'This student has not created any reports yet.')
        return redirect('teacher_dashboard')

    if request.method == 'POST':
        # Handle Override (AJAX)
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                audit_id = data.get('audit_id')
                new_status = data.get('status')
                audit = DailyGitAudit.objects.get(id=audit_id, report=report)
                audit.ai_status = new_status
                audit.save()
                return JsonResponse({'success': True, 'message': 'Status overridden successfully.'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)}, status=400)
                
        # Handle Verdict (Form POST)
        verdict = request.POST.get('verdict')
        feedback = request.POST.get('feedback', '')
        
        if feedback:
            report.supervisor_feedback = feedback
            
        if verdict == 'approve':
            report.status = 'Reviewed'
        elif verdict == 'reject':
            report.status = 'Changes Requested'
            
        report.save()
        messages.success(request, f'Report status updated to {report.status}')
        return redirect('teacher_dashboard')

    repo = student.repositories.first()
    project_title = repo.name if repo else 'CS Project'
    
    student_info = {
        'id': student.id,
        'name': student.get_full_name() or student.username,
        'avatar': f'https://ui-avatars.com/api/?name={student.username}&background=003865&color=fff',
        'project_title': project_title,
        'current_week': 8,
        'report_status': report.status,
    }

    bi_weekly_data = {
        'title': report.title,
        'intro': 'By the next meeting, you should be able to update your supervisor on:',
        'items': [
            'The <strong>final design and aims</strong> of the project',
            'Any <strong>prototyping activities</strong> undertaken',
            'The <strong>current status of your build</strong>, including a live demonstration.',
            '<strong>Dissertation progress</strong>.'
        ]
    }

    # Fetch daily audits for this report
    daily_audits = report.daily_audits.all().order_by('date')
    
    # Prepare chart data
    chart_labels = []
    chart_added = []
    chart_deleted = []
    for audit in daily_audits:
        chart_labels.append(audit.date.strftime('%Y-%m-%d'))
        chart_added.append(audit.loc_added)
        chart_deleted.append(audit.loc_deleted)

    context = {
        'student': student_info,
        'report': report,
        'bi_weekly_data': bi_weekly_data,
        'daily_audits': daily_audits,
        'milestones': report.milestones,
        'chart_labels': json.dumps(chart_labels),
        'chart_added': json.dumps(chart_added),
        'chart_deleted': json.dumps(chart_deleted)
    }
    return render(request, 'auditor/teacher_student_review.html', context)
