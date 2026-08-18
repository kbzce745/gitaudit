import os
from datetime import datetime
from django.conf import settings
from .models import Repository
from .gitlab_client import GitLabAPIClient

def fetch_weekly_diffs(student, start_date, end_date):
    """
    Fetches all commits and diffs for a student's repository between start_date and end_date.
    Groups them by day (Monday-Sunday) and calculates LOC.
    Returns a dictionary mapping date strings to aggregated diff data.
    """
    repo = Repository.objects.filter(student=student).first()
    if not repo:
        return {}
        
    private_token = os.environ.get("GITLAB_PRIVATE_TOKEN")
    # For MVP, assume stgit base URL or take from repo.url if it matches
    client = GitLabAPIClient(base_url="https://stgit.dcs.gla.ac.uk", private_token=private_token)
    
    # Ensure start and end are datetime objects if strings are passed
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        
    # Fetch commits in range
    commits = client.fetch_commits(
        project_id=repo.gitlab_project_id, 
        since=start_date, 
        until=end_date,
        fetch_all=True
    )
    
    # Dictionary to aggregate diffs by date string (YYYY-MM-DD)
    daily_data = {}
    
    for commit in commits:
        commit_date_str = commit['committed_at'][:10] # YYYY-MM-DD
        
        if commit_date_str not in daily_data:
            daily_data[commit_date_str] = {
                'raw_diff': '',
                'loc_added': 0,
                'loc_deleted': 0,
                'commits_count': 0
            }
            
        daily_data[commit_date_str]['commits_count'] += 1
        
        # Fetch the diff for this commit
        diffs = client.fetch_commit_diff(repo.gitlab_project_id, commit['commit_sha'])
        
        for diff_file in diffs:
            raw_diff_content = diff_file.get('diff', '')
            daily_data[commit_date_str]['raw_diff'] += f"\n--- a/{diff_file.get('old_path')} b/{diff_file.get('new_path')} ---\n"
            daily_data[commit_date_str]['raw_diff'] += raw_diff_content + "\n"
            
            # Simple LOC calculation from diff syntax
            for line in raw_diff_content.splitlines():
                if line.startswith('+') and not line.startswith('+++'):
                    daily_data[commit_date_str]['loc_added'] += 1
                elif line.startswith('-') and not line.startswith('---'):
                    daily_data[commit_date_str]['loc_deleted'] += 1
                    
    return daily_data
