import os
import sys
import django
from pprint import pprint

# Add the project root directory to sys.path so Python can find 'config' and 'auditor'
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Setup Django environment for consistency
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from auditor.gitlab_client import GitLabAPIClient

def run_test():
    print("--- Starting Day 2 API Fetch Test ---")
    
    # Initialize the client. 
    # Note: Pass `private_token="glpat-y4QxdOlpMh5EIhTHsRJLPm86MQp1OjR2Ywk.01.0z0s9a1ws"` if testing against a private project
    client = GitLabAPIClient(
        base_url="https://stgit.dcs.gla.ac.uk",
        private_token="glpat-y4QxdOlpMh5EIhTHsRJLPm86MQp1OjR2Ywk.01.0z0s9a1ws"
    ) 
    
    PROJECT_ID = 24961 
    
    print(f"\n[1] Testing Commit Fetching for Project {PROJECT_ID}...")
    
    # We call fetch_commits with fetch_all=True to pull ALL commits across all branches.
    # Note: If a project has thousands of commits, this might take a moment.
    cleaned_commits = client.fetch_commits(PROJECT_ID, fetch_all=True)
    
    print(f"Total commits fetched: {len(cleaned_commits)}")
    # pprint(cleaned_commits) # Uncomment if you want to see all commits again
    
    print(f"\n[2] Testing Commit Diff (Raw fetch):")
    diffs = client.fetch_commit_diff(PROJECT_ID, "34480d37c221b2c5cbe7237c7423fa59c5079a84")
    # pprint(diffs) # Uncomment to see raw diffs
    print(f"Fetched {len(diffs)} file changes.")
    
    from auditor.diff_parser import parse_commit_diff
    print(f"\n[3] Testing Tier 1 Diff Parser:")
    parsed_metrics = parse_commit_diff(diffs)
    pprint(parsed_metrics)
    
    print(f"\n[4] Testing LLM Context Builder:")
    from auditor.context_builder import LLMContextBuilder
    
    # We need a single commit metadata dict. Let's use the first one fetched.
    commit_meta = cleaned_commits[0] if cleaned_commits else {}
    
    user_prompt = LLMContextBuilder.build_commit_prompt(commit_meta, parsed_metrics)
    
    print("--- GENERATED USER PROMPT ---")
    print(user_prompt)
    print("-----------------------------")

if __name__ == "__main__":
    run_test()
