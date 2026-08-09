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
    
    # Mock Sample 1: A clean feature addition (Low Risk)
    commit_meta_1 = {
        "commit_sha": "abc12345678",
        "author_name": "Alice",
        "message": "Add user profile UI components",
        "committed_at": "2026-08-09T10:00:00Z"
    }
    metrics_1 = {
        "total_loc": 45, "cdr": 0.0, "tsr": 0.5, "gini_loc": 0.2, 
        "burstiness": 0.0, "is_anomaly": False, "anomaly_reason": [],
        "modified_functions": ["UserProfile", "test_user_profile"],
        "is_boilerplate_only": False
    }
    
    # Mock Sample 2: A risky huge refactor without tests (High Risk)
    commit_meta_2 = {
        "commit_sha": "def87654321",
        "author_name": "Bob",
        "message": "Massive refactor of database core",
        "committed_at": "2026-08-09T11:00:00Z"
    }
    metrics_2 = {
        "total_loc": 1800, "cdr": 0.4, "tsr": 0.0, "gini_loc": 0.85, 
        "burstiness": 0.0, "is_anomaly": True, "anomaly_reason": ["LOC > 1000", "Gini > 0.8"],
        "modified_functions": ["CoreDB", "MigrationEngine"],
        "is_boilerplate_only": False
    }

    # Generate Prompts
    input_1 = LLMContextBuilder.build_commit_prompt(commit_meta_1, metrics_1)
    input_2 = LLMContextBuilder.build_commit_prompt(commit_meta_2, metrics_2)
    
    # Expected Output 1
    output_1 = {
        "status": "PASS",
        "summary": "Added UserProfile UI components along with corresponding tests.",
        "risk_level": "Low",
        "anomalies": []
    }
    
    # Expected Output 2
    output_2 = {
        "status": "REJECT",
        "summary": "Massive core database refactoring lacking any test coverage.",
        "risk_level": "High",
        "anomalies": [
            "Extremely high volume of changed lines (1800 LOC).",
            "Zero test coverage (TSR=0.0) for a critical database refactor.",
            "Highly concentrated changes posing architectural risk (Gini=0.85)."
        ]
    }

    # Format into Alpaca JSONL
    # Instruction is technically the SYSTEM_PROMPT.
    alpaca_format = []
    for inp, out in [(input_1, output_1), (input_2, output_2)]:
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
