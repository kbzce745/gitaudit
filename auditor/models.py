# [STUDENT-WRITTEN]
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    # A student has one teacher supervising them
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')

    def __str__(self):
        return f"{self.user.username} ({self.role})"

class Event(models.Model):
    EVENT_TYPES = (
        ('meeting', 'Meeting Request'),
        ('ddl', 'Deadline'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('declined', 'Declined'),
    )
    title = models.CharField(max_length=255)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_events')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teacher_events')
    event_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.student.username} ({self.status})"

class Repository(models.Model):
    gitlab_project_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    url = models.URLField()
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='repositories', null=True, blank=True)

class CommitLog(models.Model):
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE)
    commit_sha = models.CharField(max_length=40, unique=True)
    author_name = models.CharField(max_length=100)
    message = models.TextField()
    committed_at = models.DateTimeField()

class AuditSession(models.Model):
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE)
    prompt_context = models.JSONField(help_text="Formatted LLM prompt input")
    llm_response = models.JSONField(null=True, blank=True, help_text="LLM parsed JSON result")
    created_at = models.DateTimeField(auto_now_add=True)

class BiWeeklyReport(models.Model):
    REPORT_STATUS = (
        ('Draft', 'Draft'),
        ('Locked', 'Locked'),
        ('Reviewed', 'Reviewed'),
        ('Changes Requested', 'Changes Requested'),
    )
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bi_weekly_reports')
    title = models.CharField(max_length=255, default='Bi-Weekly Report')
    status = models.CharField(max_length=50, choices=REPORT_STATUS, default='Draft')
    meeting_date = models.DateField(null=True, blank=True)
    milestones = models.JSONField(null=True, blank=True, help_text="List of milestone objects with status")
    
    # Textual submissions
    text_design = models.TextField(blank=True, null=True)
    text_prototype = models.TextField(blank=True, null=True)
    text_dissertation = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.student.username} ({self.status})"

class EvidenceImage(models.Model):
    report = models.ForeignKey(BiWeeklyReport, on_delete=models.CASCADE, related_name='evidence_images')
    image = models.ImageField(upload_to='evidence_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class DailyGitAudit(models.Model):
    STATUS_CHOICES = (
        ('green', 'Green'),
        ('yellow', 'Yellow'),
        ('red', 'Red'),
    )
    report = models.ForeignKey(BiWeeklyReport, on_delete=models.CASCADE, related_name='daily_audits')
    date = models.DateField()
    day_of_week = models.CharField(max_length=20)
    raw_diff = models.TextField(blank=True, null=True)
    loc_added = models.IntegerField(default=0)
    loc_deleted = models.IntegerField(default=0)
    
    # LLM Output
    llm_summary = models.TextField(blank=True, null=True)
    diff_snippet = models.TextField(blank=True, null=True)
    ai_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='green')

    class Meta:
        ordering = ['date']
        
    def __str__(self):
        return f"{self.day_of_week} ({self.date}) - {self.report.title}"
