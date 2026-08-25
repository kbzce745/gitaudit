import factory
from django.contrib.auth.models import User
from auditor.models import UserProfile, BiWeeklyReport, Repository
from django.utils import timezone

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    password = factory.PostGenerationMethodCall('set_password', 'password123')

class UserProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserProfile
    
    user = factory.SubFactory(UserFactory)
    role = 'student'
    supervisor = None

class RepositoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Repository
    
    gitlab_project_id = factory.Sequence(lambda n: 1000 + n)
    name = factory.Sequence(lambda n: f"Repo-{n}")
    url = factory.LazyAttribute(lambda o: f"https://gitlab.com/{o.name}")
    student = factory.SubFactory(UserFactory)
    access_token = "fake-token-123"

class BiWeeklyReportFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BiWeeklyReport
    
    student = factory.SubFactory(UserFactory)
    title = "Test Report"
    status = "Draft"
    text_completed = "Completed tests"
