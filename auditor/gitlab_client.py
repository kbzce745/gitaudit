# [STUDENT-WRITTEN]
import time
import requests
from urllib.parse import urljoin
import logging

logger = logging.getLogger(__name__)

class GitLabAPIClient:
    """
    GitLab REST API Client handling pagination and rate limiting.
    """
    def __init__(self, base_url="https://gitlab.com", private_token=None):
        self.base_url = base_url.rstrip('/') + '/api/v4/'
        self.session = requests.Session()
        if private_token:
            self.session.headers.update({"PRIVATE-TOKEN": private_token})

    def _request(self, method, endpoint, **kwargs):
        """
        Base request method with 429 Rate Limit retry mechanism.
        """
        url = urljoin(self.base_url, endpoint)
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            response = self.session.request(method, url, **kwargs)
            
            if response.status_code == 429:
                logger.warning(f"Rate limit exceeded (429) for {url}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                continue
                
            response.raise_for_status()
            return response
            
        raise Exception("Max retries exceeded due to rate limit (429)")

    def _paginate(self, endpoint, params=None):
        """
        Generator to handle GitLab API pagination.
        """
        if params is None:
            params = {}
        
        params['page'] = 1
        params['per_page'] = 50

        while True:
            response = self._request('GET', endpoint, params=params)
            data = response.json()
            
            if not data:
                break
                
            for item in data:
                yield item
                
            # GitLab uses link headers for pagination
            if 'next' not in response.links:
                break
                
            params['page'] += 1

    def fetch_commits(self, project_id, ref_name=None, fetch_all=False):
        """
        Fetch commits for a project, extracting and filtering core fields.
        """
        endpoint = f"projects/{project_id}/repository/commits"
        params = {}
        if fetch_all:
            params['all'] = 'true'
        elif ref_name:
            params['ref_name'] = ref_name
            
        cleaned_commits = []
        
        for commit in self._paginate(endpoint, params=params):
            cleaned_commits.append({
                "commit_sha": commit.get("id"),
                "author_name": commit.get("author_name"),
                "message": commit.get("message"),
                "committed_at": commit.get("created_at")
            })
            
        return cleaned_commits

    def fetch_merge_requests(self, project_id):
        """
        Fetch Merge Requests for a project, extracting and filtering core fields.
        """
        endpoint = f"projects/{project_id}/merge_requests"
        cleaned_mrs = []
        
        for mr in self._paginate(endpoint):
            cleaned_mrs.append({
                "mr_iid": mr.get("iid"),
                "title": mr.get("title"),
                "description": mr.get("description"),
                "author": mr.get("author", {}).get("name") if mr.get("author") else None,
                "created_at": mr.get("created_at"),
                "state": mr.get("state")
            })
            
        return cleaned_mrs
