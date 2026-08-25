import pytest
from datetime import datetime
from auditor.services import fetch_weekly_diffs, analyze_diff_with_ollama
from auditor.tests.factories import UserFactory, RepositoryFactory
from auditor.gitlab_client import GitLabAPIClient

@pytest.mark.django_db
def test_fetch_weekly_diffs_no_repo():
    student = UserFactory()
    # No repo created
    result = fetch_weekly_diffs(student, "2023-01-01", "2023-01-02")
    assert result == {}

@pytest.mark.django_db
def test_fetch_weekly_diffs_success(mocker):
    student = UserFactory()
    repo = RepositoryFactory(student=student)

    # Mock GitLabAPIClient
    mock_fetch_commits = mocker.patch.object(GitLabAPIClient, 'fetch_commits')
    mock_fetch_diff = mocker.patch.object(GitLabAPIClient, 'fetch_commit_diff')

    mock_fetch_commits.return_value = [
        {"commit_sha": "sha1", "committed_at": "2023-01-01T12:00:00Z"},
        {"commit_sha": "sha2", "committed_at": "2023-01-01T15:00:00Z"},
    ]
    
    mock_fetch_diff.side_effect = [
        [{"diff": "+ added\n- deleted\n", "old_path": "a.txt", "new_path": "a.txt"}],
        [{"diff": "+ added 2\n", "old_path": "b.txt", "new_path": "b.txt"}]
    ]

    result = fetch_weekly_diffs(student, "2023-01-01", "2023-01-02")
    
    # 2023-01-01 should have 2 commits
    day1 = result["2023-01-01"]
    assert day1["commits_count"] == 2
    assert day1["loc_added"] == 2
    assert day1["loc_deleted"] == 1
    assert "--- a/a.txt" in day1["raw_diff"]
    
    # 2023-01-02 should have 0 commits
    day2 = result["2023-01-02"]
    assert day2["commits_count"] == 0

def test_analyze_diff_empty():
    result = analyze_diff_with_ollama("")
    assert result["ai_status"] == "green"
    assert "No code changes" in result["llm_summary"]

def test_analyze_diff_success(mocker):
    mock_post = mocker.patch('requests.post')
    
    class MockResponse:
        def json(self):
            return {"response": '```json\n{"status": "WARN", "summary": "Looks weird"}\n```'}
        def raise_for_status(self):
            pass
            
    mock_post.return_value = MockResponse()

    result = analyze_diff_with_ollama("+ bad code", loc_added=1)
    
    assert result["ai_status"] == "yellow"
    assert result["llm_summary"] == "Looks weird"

def test_analyze_diff_fallback(mocker):
    # Test when the model returns bad JSON
    mock_post = mocker.patch('requests.post')
    
    class MockResponse:
        def json(self):
            return {"response": 'I think the "status": "REJECT" and "summary": "Terrible code"'}
        def raise_for_status(self):
            pass
            
    mock_post.return_value = MockResponse()

    result = analyze_diff_with_ollama("+ terrible code", loc_added=1)
    
    assert result["ai_status"] == "red"
    assert "Terrible code" in result["llm_summary"]

def test_analyze_diff_network_error(mocker):
    mock_post = mocker.patch('requests.post')
    mock_post.side_effect = Exception("Connection Refused")

    result = analyze_diff_with_ollama("+ some code")
    
    assert result["ai_status"] == "yellow"
    assert "Failed to reach local AI Engine" in result["llm_summary"]
