import os
import django
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from auditor.models import Repository, CommitLog, AuditSession

def run_test():
    print("--- Starting Day 1 Models Test ---")
    
    # 1. Create or get a Repository record
    # Using get_or_create to avoid unique=True errors on repeated runs
    repo, created = Repository.objects.get_or_create(
        gitlab_project_id=1001, 
        defaults={
            "name": "test-repo", 
            "url": "https://gitlab.example.com/test-repo"
        }
    )
    if created:
        print(f"Successfully created Repo: {repo.name}")
    else:
        print(f"Found existing Repo: {repo.name}")

    # 2. Create a CommitLog record for this repository
    commit, created = CommitLog.objects.get_or_create(
        commit_sha="abcd1234567890", 
        defaults={
            "repository": repo, 
            "author_name": "Alice", 
            "message": "Initial commit for testing", 
            "committed_at": timezone.now()
        }
    )
    if created:
        print(f"Successfully created Commit: {commit.commit_sha}")
    else:
        print(f"Found existing Commit: {commit.commit_sha}")

    # 3. Create an AuditSession record (testing JSONField)
    session = AuditSession.objects.create(
        repository=repo, 
        prompt_context={"role": "user", "content": "Please analyze this commit."}, 
        llm_response={"status": "success", "analysis": "Looks good!"}
    )
    print(f"Successfully created Session, ID: {session.id}")

    # 4. Verify database persistence
    print("\n--- Database Verification Results ---")
    print("All Repositories:", list(Repository.objects.all()))
    print("All Commits:", list(CommitLog.objects.all()))
    print("All Audit Sessions:", list(AuditSession.objects.all()))

if __name__ == "__main__":
    run_test()
