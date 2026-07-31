import json
import os
import requests
from django.conf import settings

# [STUDENT-WRITTEN]
USE_MOCK_OLLAMA_API = True
OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"

def analyze(diff: str, report: str, timeout: float = 15.0) -> dict:
    if USE_MOCK_OLLAMA_API:
        # Load from fixture
        base_dir = settings.BASE_DIR if hasattr(settings, 'BASE_DIR') else os.path.dirname(os.path.dirname(__file__))
        fixture_path = os.path.join(base_dir, 'fixtures', 'mock_ollama_response.json')
        
        with open(fixture_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    # For live API execution
    prompt = f"Analyze this diff:\n{diff}\n\nAgainst this report:\n{report}\n\nOutput only valid JSON."
    
    payload = {
        "model": "llama3", # Assuming a model like llama3
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }
    
    try:
        response = requests.post(OLLAMA_ENDPOINT, json=payload, timeout=timeout)
        response.raise_for_status()
        result_text = response.json().get('response', '{}')
        
        # Parsing Safety
        audit_json = json.loads(result_text)
        
        # Enforce strict 3-key JSON output format
        return {
            "status": audit_json.get("status", "YELLOW"),
            "score": audit_json.get("score", 0),
            "justification": audit_json.get("justification", "Missing justification")
        }
    except Exception as e:
        # Wrap response with try-except block to capture invalid JSON outputs
        raise Exception(f"AI Audit Failed: {str(e)}")
