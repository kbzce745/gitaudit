import os
import requests
import json
from datetime import datetime

# ================= Configuration Area =================
PROJECT_ID = 25004
GITLAB_TOKEN = "glpat-A_8L1WZWbnW7mhpozQw4pm86MQp1OjR2ZAk.01.0z0dyu3sz"
BASE_URL = "https://stgit.dcs.gla.ac.uk/api/v4"
OUTPUT_FILE = "dataset.json"

# ================= Fetch Logic =================
def fetch_commits():
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    url = f"{BASE_URL}/projects/{PROJECT_ID}/repository/commits?per_page=50&all=true"
    
    print(f"Fetching commits for Project {PROJECT_ID}...")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error fetching commits: {response.text}")
        return []
        
    return response.json()

def fetch_diff(commit_sha):
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    url = f"{BASE_URL}/projects/{PROJECT_ID}/repository/commits/{commit_sha}/diff"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def main():
    commits = fetch_commits()
    if not commits:
        return
        
    dataset = []
    
    for i, commit in enumerate(commits):
        sha = commit['id']
        msg = commit['message'].strip()
        print(f"[{i+1}/{len(commits)}] Processing commit {sha[:8]} - {msg.splitlines()[0][:30]}...")
        
        diffs = fetch_diff(sha)
        
        raw_diff_text = ""
        for d in diffs:
            old_path = d.get('old_path', '')
            new_path = d.get('new_path', '')
            diff_content = d.get('diff', '')
            raw_diff_text += f"--- {old_path}\n+++ {new_path}\n{diff_content}\n"
            
        # Skip empty diff
        if not raw_diff_text.strip():
            continue
            
        # Truncate overly long diff to prevent token overflow
        if len(raw_diff_text) > 3000:
            raw_diff_text = raw_diff_text[:3000] + "\n...[DIFF TRUNCATED]..."
            
        # Construct prompt
        prompt_diff = f"Commit Message: {msg}\n\n{raw_diff_text}"
        
        # Assemble Alpaca format
        item = {
            "instruction": 'Analyze this git diff and evaluate code quality/risks. You MUST return ONLY a JSON object in this exact format: {"status": "PASS" or "WARN" or "REJECT", "summary": "Your analysis"}.',
            "input": prompt_diff,
            "output": '{"status": "PASS", "summary": "This is a placeholder summary. Please replace this with human expert evaluation or use a larger LLM to generate it."}'
        }
        dataset.append(item)
        
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
        
    print(f"\n🎉 Successfully extracted {len(dataset)} commit-diff pairs and saved to {OUTPUT_FILE}!")
    print("Now you can fill in the 'output' fields with high-quality reviews to train your LoRA model.")

if __name__ == "__main__":
    main()
