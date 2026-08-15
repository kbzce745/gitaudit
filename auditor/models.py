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
