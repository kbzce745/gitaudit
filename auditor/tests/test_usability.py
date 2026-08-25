from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from auditor.models import UserProfile, BiWeeklyReport

class UsabilityTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create Teacher
        self.teacher = User.objects.create_user(username='teacher', password='password123')
        UserProfile.objects.create(user=self.teacher, role='teacher')

        # Create Student
        self.student = User.objects.create_user(username='student', password='password123')
        UserProfile.objects.create(user=self.student, role='student', supervisor=self.teacher)

    def test_login_page_renders(self):
        """Test if the login page renders correctly (HTTP 200)."""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "GitAudit")

    def test_student_login_and_dashboard(self):
        """Test student login flow and dashboard rendering."""
        # Login
        login_success = self.client.login(username='student', password='password123')
        self.assertTrue(login_success)

        # Access dashboard
        response = self.client.get(reverse('student_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Student Dashboard")

    def test_teacher_login_and_dashboard(self):
        """Test teacher login flow and dashboard rendering."""
        login_success = self.client.login(username='teacher', password='password123')
        self.assertTrue(login_success)

        # Access dashboard
        response = self.client.get(reverse('teacher_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Supervisor Dashboard")

    def test_student_report_submission(self):
        """Test if a student can submit a bi-weekly report."""
        self.client.login(username='student', password='password123')
        
        # Post data to simulate saving a draft
        post_data = {
            'action': 'save_draft',
            'completed': 'Finished UI tests',
            'design': 'Work on backend next week',
            'prototype': 'No blockers',
            'agenda': 'Review UI changes'
        }
        
        response = self.client.post(reverse('student_dashboard'), data=post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Verify the report was created in the database
        report = BiWeeklyReport.objects.filter(student=self.student).first()
        self.assertIsNotNone(report)
        self.assertEqual(report.text_completed, 'Finished UI tests')
        self.assertEqual(report.status, 'Draft')

    def test_teacher_review_page(self):
        """Test if teacher can access the review page for a specific student."""
        # Create a report for the student
        BiWeeklyReport.objects.create(
            student=self.student,
            title="Test Report",
            status="Locked",
            text_completed="Done"
        )
        
        self.client.login(username='teacher', password='password123')
        response = self.client.get(reverse('teacher_student_review', args=[self.student.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Supervisor Verdict")
