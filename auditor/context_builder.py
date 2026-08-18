# [STUDENT-WRITTEN]
import json

class LLMContextBuilder:
    """
    Builds formatted prompts for the LLM based on extracted Git data and diff metrics.
    """
    
    # Force LLM to output standard JSON System Prompt
    SYSTEM_PROMPT = """
You are an expert code audit assistant. Your task is to analyze the provided git commit metadata and Tier 1 diff metrics.

CRITICAL INSTRUCTION: Your response MUST be a single, valid JSON object. Do NOT wrap it in markdown code blocks (e.g. ```json). Do NOT add any conversational text before or after the JSON.

The JSON object MUST contain exactly the following keys:
- "status": A string indicating the audit result. Must be exactly one of ["PASS", "WARN", "REJECT"].
- "summary": A one-sentence natural language summary of what the code changes accomplish.
- "risk_level": A string indicating the risk level. Must be exactly one of ["Low", "Medium", "High"].
- "anomalies": A list of strings describing any potential issues, bugs, or architectural anomalies found. (Empty list if none)

Example of expected output:
{
  "status": "WARN",
  "summary": "Added a new database migration and modified authentication logic.",
  "risk_level": "Medium",
  "anomalies": ["Authentication middleware lacks robust error handling"]
}
"""

    @staticmethod
    def build_commit_prompt(commit_meta, parsed_metrics):
        """
        Constructs the user prompt containing commit metadata and parsed Tier 1 metrics.
        """
        # Assembling Context Data Structures
        prompt_data = {
            "commit_info": {
                "sha": commit_meta.get("commit_sha", ""),
                "author": commit_meta.get("author_name", ""),
                "message": commit_meta.get("message", ""),
                "date": str(commit_meta.get("committed_at", ""))
            },
            "diff_metrics": parsed_metrics
        }
        
        user_prompt = f"""
Please audit the following commit based on its metadata and Tier 1 diff metrics.

Commit Data:
{json.dumps(prompt_data, indent=2, ensure_ascii=False)}

Analyze the metrics carefully. Pay special attention to 'is_anomaly', 'tsr' (Test to Source Ratio), and 'cdr' (Code Deletion Ratio). 
Determine the appropriate risk level and status, and extract any anomalies. Provide your response purely as the requested JSON object.
"""
        return user_prompt.strip()
