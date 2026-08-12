import os
import sys
import django
import requests
import io
from pprint import pprint

# Force UTF-8 encoding for Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf8', errors='ignore')

# Add the project root directory to sys.path so Python can find 'config' and 'auditor'
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from auditor.gitlab_client import GitLabAPIClient
from auditor.diff_parser import parse_commit_diff
from auditor.context_builder import LLMContextBuilder
from auditor.llm_parser import LLMJSONParser

def run_real_commit_audit():
    print("--- Starting Real Commit Audit with Local Ollama ---")
    
    # 1. Initialize the GitLab client
    client = GitLabAPIClient(
        base_url="https://stgit.dcs.gla.ac.uk",
        private_token="glpat-y4QxdOlpMh5EIhTHsRJLPm86MQp1OjR2Ywk.01.0z0s9a1ws"
    ) 
    
    PROJECT_ID = 24961 
    # Here i am using a specific commit from my earlier test:
    TARGET_COMMIT_SHA = "0e113034528ed4e1be23610d3c5be3b34e15ee83"
    
    print(f"\n[1] Fetching Commit Metadata for {TARGET_COMMIT_SHA}...")
    # Fetch all commits and find the one we want (or just use the first one if not found)
    commits = client.fetch_commits(PROJECT_ID, fetch_all=False)
    target_commit_meta = next((c for c in commits if c["commit_sha"] == TARGET_COMMIT_SHA), commits[0] if commits else {})
    print(f"Author: {target_commit_meta.get('author_name')}")
    print(f"Message: {target_commit_meta.get('message')}")
    
    print(f"\n[2] Fetching Commit Diff and Parsing Metrics...")
    diffs = client.fetch_commit_diff(PROJECT_ID, target_commit_meta.get("commit_sha"))
    parsed_metrics = parse_commit_diff(diffs)
    print(f"Tier 1 Metrics Extracted: LOC={parsed_metrics.get('total_loc')}, TSR={parsed_metrics.get('tsr')}")
    
    print(f"\n[3] Building LLM Context Prompt...")
    user_prompt = LLMContextBuilder.build_commit_prompt(target_commit_meta, parsed_metrics)
    
    print(f"\n[4] Sending to Local Ollama (gitaudit_model)...")
    try:
        response = requests.post('http://localhost:11434/api/generate', json={
            'model': 'gitaudit_model',
            'prompt': user_prompt,
            'stream': False
        })
        response.raise_for_status()
        llm_raw_output = response.json().get('response', '')
        
        print("\n--- RAW LLM OUTPUT ---")
        print(llm_raw_output)
        print("-------------------------\n")
        
        print(f"[5] Parsing LLM Output with LLMJSONParser...")
        final_audit_report = LLMJSONParser.parse_response(llm_raw_output)
        
        print("--- FINAL STRUCTURED AUDIT REPORT ---")
        pprint(final_audit_report)
        print("-----------------------------------------")
        
    except requests.exceptions.ConnectionError:
        print("\n Error: Cannot connect to Ollama. Is Ollama running on your machine? Try running 'ollama serve' in another terminal.")
    except Exception as e:
        print(f"\n Unexpected error: {e}")

if __name__ == "__main__":
    run_real_commit_audit()
