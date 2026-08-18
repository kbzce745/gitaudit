import os
import django
import csv

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from auditor.models import UserProfile, Repository

def run():
    print("Loading users from mock_users.csv...")
    
    with open('mock_users.csv', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            username = row['name'].replace(' ', '').lower()
            email = row['email']
            password = row['password']
            role = row['role']
            
            # Create User
            user, created = User.objects.get_or_create(username=username, defaults={'email': email})
            if created:
                user.set_password(password)
                user.first_name = row['name'].split()[0]
                if len(row['name'].split()) > 1:
                    user.last_name = row['name'].split()[1]
                user.save()
                print(f"Created user: {username} ({role})")
            else:
                # Update password just in case
                user.set_password(password)
                user.save()
                
            # Create UserProfile
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = role
            
            if role == 'student' and row['supervisor_email']:
                try:
                    supervisor = User.objects.get(email=row['supervisor_email'])
                    profile.supervisor = supervisor
                except User.DoesNotExist:
                    print(f"Warning: Supervisor {row['supervisor_email']} not found for {username}")
            profile.save()

            # Create Repository for student
            if role == 'student' and row['gitlab_project_id']:
                repo, repo_created = Repository.objects.get_or_create(
                    gitlab_project_id=int(row['gitlab_project_id']),
                    defaults={
                        'name': row['repo_name'],
                        'url': row['repo_url'],
                        'student': user
                    }
                )
                if repo_created:
                    print(f"  Created repository for {username}: {repo.name}")
                else:
                    repo.student = user
                    repo.save()
                    
    print("Done loading data!")

if __name__ == '__main__':
    run()
