# [STUDENT-WRITTEN]
import json
import re
import logging

logger = logging.getLogger(__name__)

class LLMJSONParser:
    """
    A robust parser designed to extract and validate JSON outputs from LLMs.
    It handles common LLM hallucination patterns such as wrapping JSON in Markdown blocks
    or adding conversational filler text.
    """
    
    REQUIRED_KEYS = {"status", "summary", "risk_level", "anomalies"}
    VALID_STATUS = {"PASS", "WARN", "REJECT"}
    VALID_RISK = {"Low", "Medium", "High"}

    @classmethod
    def parse_response(cls, raw_text: str) -> dict:
        """
        Extracts JSON from the raw LLM output and validates it.
        Returns a dictionary with the parsed data or a fallback error dict if parsing fails.
        """
        if not raw_text or not isinstance(raw_text, str):
            return cls._fallback_response("Empty or invalid response from LLM.")

        cleaned_text = cls._clean_text(raw_text)
        
        try:
            parsed_data = json.loads(cleaned_text)
            return cls._validate_data(parsed_data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from LLM: {e}. Raw text: {raw_text}")
            return cls._fallback_response("LLM output was not valid JSON.")

    @classmethod
    def _clean_text(cls, text: str) -> str:
        """
        Uses regex to extract JSON content even if the LLM wrapped it in Markdown
        or added conversational filler.
        """
        # Strip leading/trailing whitespace
        text = text.strip()
        
        # Regex to find content between the first '{' and the last '}'
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return match.group(0)
            
        return text # If no match, return as is (json.loads might still work or fail naturally)

    @classmethod
    def _validate_data(cls, data: dict) -> dict:
        """
        Validates the structure and enum values of the parsed JSON.
        If validation fails, falls back to a safe default.
        """
        if not isinstance(data, dict):
            return cls._fallback_response("Parsed JSON is not a dictionary.")
            
        # Check required keys
        if not cls.REQUIRED_KEYS.issubset(data.keys()):
            missing = cls.REQUIRED_KEYS - data.keys()
            return cls._fallback_response(f"Missing required keys in LLM output: {missing}")
            
        # Validate ENUMs
        if data.get("status") not in cls.VALID_STATUS:
            data["status"] = "WARN" # Safe fallback
            if isinstance(data.get("anomalies"), list):
                data["anomalies"].append("System Warning: Invalid status enum returned by LLM.")
            else:
                data["anomalies"] = ["System Warning: Invalid status enum returned by LLM."]
            
        if data.get("risk_level") not in cls.VALID_RISK:
            data["risk_level"] = "Medium" # Safe fallback
            if isinstance(data.get("anomalies"), list):
                data["anomalies"].append("System Warning: Invalid risk_level enum returned by LLM.")
            else:
                data["anomalies"] = ["System Warning: Invalid risk_level enum returned by LLM."]
            
        # Ensure anomalies is a list
        if not isinstance(data.get("anomalies"), list):
            data["anomalies"] = []
            
        return data

    @classmethod
    def _fallback_response(cls, reason: str) -> dict:
        """
        Returns a safe, neutral fallback dictionary if the LLM completely fails.
        Prevents the Django WebApp from crashing.
        """
        return {
            "status": "WARN",
            "summary": "Automatic audit failed due to parsing error. Manual review required.",
            "risk_level": "Medium",
            "anomalies": [f"System Error: {reason}"]
        }
