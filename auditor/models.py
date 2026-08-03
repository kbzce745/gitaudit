# ==============================================================================
# STUDENT-ATTRIBUTION
# ==============================================================================
from django.db import models

class Repository(models.Model):
    gitlab_project_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    url = models.URLField()

class CommitLog(models.Model):
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE)
    commit_sha = models.CharField(max_length=40, unique=True)
    author_name = models.CharField(max_length=100)
    message = models.TextField()
    committed_at = models.DateTimeField()

class AuditSession(models.Model):
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE)
    prompt_context = models.JSONField(help_text="格式化的 LLM 提示词输入")
    llm_response = models.JSONField(null=True, blank=True, help_text="LLM 解析后的 JSON 结果")
    created_at = models.DateTimeField(auto_now_add=True)
