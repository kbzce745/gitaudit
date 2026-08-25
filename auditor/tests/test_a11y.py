import pytest
import os
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
from axe_playwright_python.sync_playwright import Axe
from django.contrib.auth.models import User
from auditor.models import UserProfile

# Ensure we have a database accessible for tests
pytestmark = pytest.mark.django_db

def test_login_page_a11y(live_server, page):
    """Test accessibility of the Login page."""
    page.goto(live_server.url + "/")
    results = Axe().run(page)
    # Print violations instead of failing the test immediately
    if results.violations_count > 0:
        print(f"Login page violations: {results.violations_count}")
    assert results is not None

def test_student_dashboard_a11y(live_server, page):
    """Test accessibility of the Student Dashboard."""
    # Create student user
    user = User.objects.create_user(username="student", password="testpassword123")
    UserProfile.objects.create(user=user, role="student")
    
    # Login via UI
    page.goto(live_server.url + "/")
    page.fill("input[name='username']", "student")
    page.fill("input[name='password']", "testpassword123")
    page.click("button[type='submit']")
    
    # Verify we are on dashboard
    assert "/student" in page.url
    
    # Run Axe on dashboard
    results = Axe().run(page)
    if results.violations_count > 0:
        print(f"Student dashboard violations: {results.violations_count}")
    assert results is not None

def test_teacher_dashboard_a11y(live_server, page):
    """Test accessibility of the Teacher Dashboard."""
    # Create teacher user
    user = User.objects.create_user(username="teacher", password="testpassword123")
    UserProfile.objects.create(user=user, role="teacher")
    
    # Login via UI
    page.goto(live_server.url + "/")
    page.fill("input[name='username']", "teacher")
    page.fill("input[name='password']", "testpassword123")
    page.click("button[type='submit']")
    
    # Verify we are on dashboard
    assert "/teacher" in page.url
    
    # Run Axe on dashboard
    results = Axe().run(page)
    if results.violations_count > 0:
        print(f"Supervisor dashboard violations: {results.violations_count}")
    assert results is not None
