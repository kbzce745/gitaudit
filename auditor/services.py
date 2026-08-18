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
            
            for line in raw_diff_content.splitlines():
                if line.startswith('+') and not line.startswith('+++'):
                    daily_data[commit_date_str]['loc_added'] += 1
                elif line.startswith('-') and not line.startswith('---'):
                    daily_data[commit_date_str]['loc_deleted'] += 1
                    
    return daily_data

import requests
import json
import logging

logger = logging.getLogger(__name__)

def analyze_diff_with_ollama(diff_text):
    """
    Sends the raw git diff to the local Ollama instance (gitaudit_lora model).
    Returns a parsed JSON object containing the model's analysis.
    """
    if not diff_text or not diff_text.strip():
        return {
            "ai_status": "green",
            "llm_summary": "No code changes found.",
            "diff_snippet": ""
        }

    ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    url = f"{ollama_host}/api/generate"
    
    # Truncate diff if it's too massive to avoid blowing up context limits
    max_diff_len = 3000
    if len(diff_text) > max_diff_len:
        prompt_diff = diff_text[:max_diff_len] + "\n...[DIFF TRUNCATED]..."
    else:
        prompt_diff = diff_text
        
    payload = {
        "model": "gitaudit_lora",
        "prompt": f"Analyze this git diff and evaluate code quality/risks:\n\n{prompt_diff}",
        "stream": False,
        "options": {
            "temperature": 0.1 # Keep it deterministic
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        # The model is strictly instructed to return JSON
        model_output = result.get("response", "")
        # Strip any accidental markdown formatting (```json ... ```)
        if "```json" in model_output:
            model_output = model_output.split("```json")[1].split("```")[0].strip()
        elif "```" in model_output:
            model_output = model_output.replace("```", "").strip()
            
        parsed = json.loads(model_output)
        
        # Map PASS/WARN/REJECT to green/yellow/red
        raw_status = parsed.get("status", "PASS").upper()
        if raw_status == "REJECT":
            ai_status = "red"
        elif raw_status == "WARN":
            ai_status = "yellow"
        else:
            ai_status = "green"
            
        return {
            "ai_status": ai_status,
            "llm_summary": parsed.get("summary", "Analysis completed."),
            "diff_snippet": prompt_diff[:1000] # Provide a chunk of code for UI reference
        }
        
    except Exception as e:
        logger.error(f"Ollama API Error: {str(e)}")
        # Graceful degradation on failure
        return {
            "ai_status": "yellow",
            "llm_summary": f"Failed to reach local AI Engine: {str(e)}",
            "diff_snippet": diff_text[:500]
        }

