from django.db import models

# [STUDENT-WRITTEN]
class CommitTelemetry(models.Model):
    commit_hash = models.CharField(max_length=40, unique=True)
    author_name = models.CharField(max_length=100)
    commit_message = models.TextField()
    raw_diff = models.TextField()
    committed_at = models.DateTimeField()

# [AI-GENERATED: Antigravity, 2026-07-30]
class AuditResult(models.Model):
    telemetry = models.OneToOneField(CommitTelemetry, on_delete=models.CASCADE)
    status = models.CharField(max_length=10) # GREEN / YELLOW / RED
    score = models.IntegerField()
    justification = models.TextField()
    manual_override_status = models.CharField(max_length=10, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
