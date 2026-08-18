import json
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from auditor.context_builder import LLMContextBuilder

def generate_mock_dataset():
    """
    Generate synthetic data in Alpaca JSONL format for SFT.
    In a real scenario, you would fetch real commits, manually label their
    ideal JSON output, and feed them into this dataset.
    """
    dataset = []
    
    # --- SAMPLE 1: Clean small feature (Low Risk) ---
    commit_meta_1 = {"commit_sha": "abc001", "author_name": "Alice", "message": "Add user profile UI components", "committed_at": "2026-08-09T10:00:00Z"}
    metrics_1 = {"total_loc": 45, "cdr": 0.0, "tsr": 0.5, "burstiness": 0.0, "is_anomaly": False, "anomaly_reason": [], "modified_functions": ["UserProfile"], "is_boilerplate_only": False}
    output_1 = {"status": "PASS", "summary": "Added UserProfile UI components along with corresponding tests.", "risk_level": "Low", "anomalies": []}

    # --- SAMPLE 2: Well-tested medium feature (Low Risk) ---
    # Teaching the model that ~250 lines is totally fine if TSR is good.
    commit_meta_2 = {"commit_sha": "abc002", "author_name": "Alice", "message": "Implement OAuth2 login flow", "committed_at": "2026-08-09T10:15:00Z"}
    metrics_2 = {"total_loc": 250, "cdr": 0.1, "tsr": 0.85, "burstiness": 0.0, "is_anomaly": False, "anomaly_reason": [], "modified_functions": ["OAuthService", "LoginView"], "is_boilerplate_only": False}
    output_2 = {"status": "PASS", "summary": "Implemented OAuth2 authentication with excellent test coverage.", "risk_level": "Low", "anomalies": []}

    # --- SAMPLE 3: Huge boilerplate/auto-generated code (Low Risk) ---
    # Teaching the model to ignore huge LOC if it's just boilerplate.
    commit_meta_3 = {"commit_sha": "abc003", "author_name": "Bot", "message": "Update package-lock.json and auto-generated API clients", "committed_at": "2026-08-09T10:30:00Z"}
    metrics_3 = {"total_loc": 1500, "cdr": 0.5, "tsr": 0.0, "burstiness": 0.0, "is_anomaly": False, "anomaly_reason": [], "modified_functions": [], "is_boilerplate_only": True}
    output_3 = {"status": "PASS", "summary": "Routine update of auto-generated boilerplate and lockfiles.", "risk_level": "Low", "anomalies": []}

    # --- SAMPLE 4: Medium sized commit with ZERO tests (Medium Risk) ---
    # Teaching the model that 300 lines without tests is a warning.
    commit_meta_4 = {"commit_sha": "abc004", "author_name": "Bob", "message": "Add payment gateway webhook listener", "committed_at": "2026-08-09T10:45:00Z"}
    metrics_4 = {"total_loc": 320, "cdr": 0.0, "tsr": 0.0, "burstiness": 0.0, "is_anomaly": False, "anomaly_reason": [], "modified_functions": ["PaymentWebhook"], "is_boilerplate_only": False}
    output_4 = {"status": "WARN", "summary": "Added payment webhook listener without any test coverage.", "risk_level": "Medium", "anomalies": ["Moderate volume of added code (320 LOC) with zero test coverage (TSR=0.0)."]}

    # --- SAMPLE 5: Small commit but highly concentrated/complex (Medium Risk) ---
    
    commit_meta_5 = {"commit_sha": "abc005", "author_name": "Charlie", "message": "Refactor core encryption algorithm", "committed_at": "2026-08-09T11:00:00Z"}
    metrics_5 = {"total_loc": 120, "cdr": 0.2, "tsr": 0.5, "burstiness": 0.0, "is_anomaly": False, "anomaly_reason": [], "modified_functions": ["EncryptData"], "is_boilerplate_only": False}
    output_5 = {"status": "WARN", "summary": "Refactored encryption algorithm with highly concentrated changes.", "risk_level": "Medium", "anomalies": ["Changes are highly concentrated indicating potential bottleneck."]}

    # --- SAMPLE 6: Massive risky refactor (High Risk) ---
    commit_meta_6 = {"commit_sha": "abc006", "author_name": "Bob", "message": "Massive rewrite of database models", "committed_at": "2026-08-09T11:30:00Z"}
    metrics_6 = {"total_loc": 1800, "cdr": 0.4, "tsr": 0.0, "burstiness": 0.0, "is_anomaly": True, "anomaly_reason": ["LOC > 1000", ], "modified_functions": ["CoreDB"], "is_boilerplate_only": False}
    output_6 = {"status": "REJECT", "summary": "Massive core database refactoring lacking any test coverage.", "risk_level": "High", "anomalies": ["Extremely high volume of changed lines (1800 LOC).", "Zero test coverage (TSR=0.0) for a critical database refactor.", "Highly concentrated changes posing architectural risk."]}

    # --- SAMPLE 7: High Code Deletion with Anomaly (High Risk) ---
    commit_meta_7 = {"commit_sha": "abc007", "author_name": "Eve", "message": "Remove deprecated API v1 completely", "committed_at": "2026-08-09T12:00:00Z"}
    metrics_7 = {"total_loc": 2500, "cdr": 0.95, "tsr": 0.0, "burstiness": 1.0, "is_anomaly": True, "anomaly_reason": ["Burstiness = 1.0", "CDR > 0.8"], "modified_functions": ["APIv1"], "is_boilerplate_only": False}
    output_7 = {"status": "REJECT", "summary": "Massive deletion of API v1 code triggering anomaly alerts.", "risk_level": "High", "anomalies": ["Extremely high code deletion ratio (CDR=0.95) across 2500 lines.", "Sudden burst of activity (Burstiness=1.0) indicating potentially uncoordinated mass deletion."]}

    # Generate Prompts
    samples = [
        (commit_meta_1, metrics_1, output_1),
        (commit_meta_2, metrics_2, output_2),
        (commit_meta_3, metrics_3, output_3),
        (commit_meta_4, metrics_4, output_4),
        (commit_meta_5, metrics_5, output_5),
        (commit_meta_6, metrics_6, output_6),
        (commit_meta_7, metrics_7, output_7),
    ]

    alpaca_format = []
    for meta, metrics, out in samples:
        inp = LLMContextBuilder.build_commit_prompt(meta, metrics)
        alpaca_format.append({
            "instruction": LLMContextBuilder.SYSTEM_PROMPT.strip(),
            "input": inp,
            "output": json.dumps(out, indent=2, ensure_ascii=False)
        })

    # Write to file
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gitaudit_sft_dataset.jsonl")
    with open(output_path, 'w', encoding='utf-8') as f:
        for entry in alpaca_format:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            
    print(f"[SUCCESS] Successfully generated SFT dataset at: {output_path}")
    print(f"Generated {len(alpaca_format)} samples.")

if __name__ == "__main__":
    generate_mock_dataset()
