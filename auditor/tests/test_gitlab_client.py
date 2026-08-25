import pytest
from auditor.gitlab_client import GitLabAPIClient
from requests.exceptions import RequestException
import requests

class MockResponse:
    def __init__(self, json_data, status_code, links=None):
        self.json_data = json_data
        self.status_code = status_code
        self.links = links or {}

    def json(self):
        return self.json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"HTTP {self.status_code}")

@pytest.fixture
def gitlab_client():
    return GitLabAPIClient(private_token="fake_token")

def test_request_success(gitlab_client, mocker):
    mock_request = mocker.patch.object(gitlab_client.session, 'request')
    mock_request.return_value = MockResponse({"key": "value"}, 200)

    response = gitlab_client._request('GET', 'some/endpoint')
    assert response.status_code == 200
    assert response.json() == {"key": "value"}
    mock_request.assert_called_once()

def test_request_rate_limit_retry(gitlab_client, mocker):
    mock_request = mocker.patch.object(gitlab_client.session, 'request')
    mock_sleep = mocker.patch('time.sleep')
    
    # 1st call: 429, 2nd call: 200
    mock_request.side_effect = [
        MockResponse({}, 429),
        MockResponse({"key": "success"}, 200)
    ]

    response = gitlab_client._request('GET', 'some/endpoint')
    assert response.status_code == 200
    assert response.json() == {"key": "success"}
    assert mock_request.call_count == 2
    mock_sleep.assert_called_once_with(2)

def test_request_max_retries_exceeded(gitlab_client, mocker):
    mock_request = mocker.patch.object(gitlab_client.session, 'request')
    mock_sleep = mocker.patch('time.sleep')
    
    # Always 429
    mock_request.return_value = MockResponse({}, 429)

    with pytest.raises(Exception, match="Max retries exceeded due to rate limit"):
        gitlab_client._request('GET', 'some/endpoint')

    assert mock_request.call_count == 3
    assert mock_sleep.call_count == 3

def test_request_exception(gitlab_client, mocker):
    mock_request = mocker.patch.object(gitlab_client.session, 'request')
    mock_request.side_effect = RequestException("Connection timeout")

    with pytest.raises(Exception, match="GitLab connection failed"):
        gitlab_client._request('GET', 'some/endpoint')

def test_paginate_single_page(gitlab_client, mocker):
    mock_request = mocker.patch.object(gitlab_client, '_request')
    mock_request.return_value = MockResponse([{"id": 1}, {"id": 2}], 200)

    results = list(gitlab_client._paginate('some/endpoint'))
    assert len(results) == 2
    assert results[0]['id'] == 1
    mock_request.assert_called_once()

def test_paginate_multiple_pages(gitlab_client, mocker):
    mock_request = mocker.patch.object(gitlab_client, '_request')
    
    # 1st page has 'next' link, 2nd page has no 'next' link
    mock_request.side_effect = [
        MockResponse([{"id": 1}], 200, links={'next': {'url': 'http://next'}}),
        MockResponse([{"id": 2}], 200)
    ]

    results = list(gitlab_client._paginate('some/endpoint'))
    assert len(results) == 2
    assert results[1]['id'] == 2
    assert mock_request.call_count == 2

def test_fetch_commits(gitlab_client, mocker):
    mock_paginate = mocker.patch.object(gitlab_client, '_paginate')
    mock_paginate.return_value = iter([
        {"id": "sha1", "author_name": "Alice", "message": "First", "created_at": "2023-01-01T00:00:00Z"},
        {"id": "sha2", "author_name": "Bob", "message": "Second", "created_at": "2023-01-02T00:00:00Z"}
    ])

    commits = gitlab_client.fetch_commits(1234, fetch_all=True)
    assert len(commits) == 2
    assert commits[0]['commit_sha'] == "sha1"
    assert commits[1]['author_name'] == "Bob"

def test_fetch_commit_diff(gitlab_client, mocker):
    mock_paginate = mocker.patch.object(gitlab_client, '_paginate')
    mock_paginate.return_value = iter([
        {"diff": "+ added line\n- removed line"},
        {"diff": "+ another added line"}
    ])

    diffs = gitlab_client.fetch_commit_diff(1234, "sha1")
    assert len(diffs) == 2
    assert "added line" in diffs[0]["diff"]
