import datetime
from django.core.management.base import BaseCommand
from poc.gitlab_service import get_telemetry
from poc.audit_service import analyze
from poc.models import CommitTelemetry, AuditResult

# [STUDENT-WRITTEN]
class Command(BaseCommand):
    help = "Run the end-to-end GitAudit PoC Feasibility Verification Pipeline"

    def add_arguments(self, parser):
        parser.add_argument(
            '--simulate-timeout',
            action='store_true',
            help='Simulate a slow LLM response to trigger timeout fallback',
        )

    def handle(self, *args, **options):
        project_id = "demo_project"
        student_report_text = "Some report about database connections."
        
        self.stdout.write(self.style.NOTICE("--- Starting GitAudit PoC Pipeline ---"))
        
        # 1. Fetch GitLab telemetry (or Mock)
        self.stdout.write("1. Retrieving GitLab data......")
        try:
            telemetry_data = get_telemetry(project_id)
            self.stdout.write(self.style.SUCCESS(f"   Success! Fetched commit: {telemetry_data['commit_hash']}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   Failed to fetch GitLab data: {e}"))
            return

        # 2. Call Ollama with timeout protection
        self.stdout.write("2. Calling Ollama Audit Engine...")
        audit_json = None
        try:
            if options['simulate_timeout']:
                # Raise an exception to simulate a timeout block failing
                raise Exception("ReadTimeout: Simulated slow response (>15s)")
                
            audit_json = analyze(
                diff=telemetry_data["raw_diff"], 
                report=student_report_text,
                timeout=15.0 # Force abort if LLM takes > 15 seconds
            )
            self.stdout.write(self.style.SUCCESS(f"   Success! AI Status: {audit_json['status']}, Score: {audit_json['score']}"))
        except Exception as e:
            # Fallback mechanism for LLM timeout/failure
            self.stdout.write(self.style.WARNING(f"   AI Audit Intercepted (Fallback Triggered): {e}"))
            audit_json = {
                "status": "YELLOW",
                "score": 0,
                "justification": f"AI Audit Timed Out / Intercepted: {str(e)}"
            }

        # 3. Save to PostgreSQL (SQLite for PoC)
        self.stdout.write("3. Saving to Database...")
        try:
            telemetry, created = CommitTelemetry.objects.get_or_create(
                commit_hash=telemetry_data['commit_hash'],
                defaults={
                    'author_name': telemetry_data['author_name'],
                    'commit_message': telemetry_data['commit_message'],
                    'raw_diff': telemetry_data['raw_diff'],
                    'committed_at': telemetry_data['committed_at']
                }
            )
            
            # If existed, update fields
            if not created:
                telemetry.author_name = telemetry_data['author_name']
                telemetry.commit_message = telemetry_data['commit_message']
                telemetry.raw_diff = telemetry_data['raw_diff']
                telemetry.committed_at = telemetry_data['committed_at']
                telemetry.save()

            AuditResult.objects.update_or_create(
                telemetry=telemetry,
                defaults={
                    'status': audit_json['status'],
                    'score': audit_json['score'],
                    'justification': audit_json['justification']
                }
            )
            self.stdout.write(self.style.SUCCESS("   Success! Data persisted correctly."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   Failed to save to Database: {e}"))
            return

        self.stdout.write(self.style.SUCCESS("--- Pipeline Completed Successfully ---"))
