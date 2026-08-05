import os
import django
from pprint import pprint

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
    pprint(cleaned_commits)

if __name__ == "__main__":
    run_test()
