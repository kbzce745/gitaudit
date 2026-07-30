import json
import os
from django.conf import settings

# [STUDENT-WRITTEN]
USE_MOCK_GITLAB_API = True

def get_telemetry(project_id: str) -> dict:
    if USE_MOCK_GITLAB_API:
        # Load from fixture
        base_dir = settings.BASE_DIR if hasattr(settings, 'BASE_DIR') else os.path.dirname(os.path.dirname(__file__))
        fixture_path = os.path.join(base_dir, 'fixtures', 'mock_gitlab_commit.json')
        
        with open(fixture_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    # For live API (placeholder for future implementation)
    raise NotImplementedError("Live GitLab API fetching is not implemented in this PoC yet.")
