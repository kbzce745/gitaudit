import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Setup sys.path to find project modules
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Setup minimal Django settings for testing if required by imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from auditor.gitlab_client import GitLabAPIClient
from auditor.diff_parser import parse_commit_diff
from auditor.context_builder import LLMContextBuilder

class TestEndToEndMock(unittest.TestCase):
    
    @patch('requests.Session.request')
    def test_full_pipeline_mock(self, mock_request):
        """
        Test the entire pipeline from API fetching to LLM prompt generation 
        using mocked network responses.
        """
        # 1. Mocking the API responses
        # Mock Response 1: fetch_commits
        mock_resp_commits = MagicMock()
        mock_resp_commits.status_code = 200
        mock_resp_commits.headers = {'X-Next-Page': ''}
        mock_resp_commits.json.return_value = [
            {
                "id": "mock_sha_12345",
                "author_name": "Test Author",
                "message": "Mocked commit message",
                "created_at": "2026-08-07T12:00:00.000Z"
            }
        ]
        
        # Mock Response 2: fetch_commit_diff
        mock_resp_diff = MagicMock()
        mock_resp_diff.status_code = 200
        mock_resp_diff.headers = {'X-Next-Page': ''}
        mock_resp_diff.json.return_value = [
            {
                "new_path": "src/test_logic.py",
                "old_path": "src/test_logic.py",
                "diff": "@@ -1,3 +1,4 @@\n import os\n+import sys\n-print('hello')\n+print('world')\n+print('new line')\n+def new_test_function():\n+    pass"
            }
        ]
        mock_request.side_effect = [mock_resp_commits, mock_resp_diff]
        
        client = GitLabAPIClient(base_url="https://stgit.dcs.gla.ac.uk", private_token="fake_token")
        
        # Step 1: Fetch Commits (Mocked)
        commits = client.fetch_commits("12345")
        self.assertEqual(len(commits), 1)
        self.assertEqual(commits[0]["commit_sha"], "mock_sha_12345")
        
        # Step 2: Fetch Diff (Mocked)
        diffs = client.fetch_commit_diff("12345", "mock_sha_12345")
        self.assertEqual(len(diffs), 1)
        self.assertEqual(diffs[0]["new_path"], "src/test_logic.py")
        
        # Step 3: Parse Diff (Tier 1 Metrics)
        parsed_metrics = parse_commit_diff(diffs)
        self.assertEqual(parsed_metrics["total_loc"], 6)  # 5 added, 1 deleted
        self.assertIn("new_test_function", parsed_metrics["modified_functions"])
        
        # Step 4: Build Context Prompt
        prompt = LLMContextBuilder.build_commit_prompt(commits[0], parsed_metrics)
        
        # Verify prompt integration
        self.assertIn("mock_sha_12345", prompt)
        self.assertIn("new_test_function", prompt)
        self.assertIn("Test Author", prompt)
        
        print("\n--- Mock Integration Test Completed Successfully ---")

if __name__ == '__main__':
    unittest.main()
