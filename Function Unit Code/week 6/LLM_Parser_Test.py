import os
import sys
import unittest

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from auditor.llm_parser import LLMJSONParser

class TestLLMJSONParser(unittest.TestCase):
    
    def test_clean_json_parsing(self):
        """Test parsing of perfect, clean JSON"""
        raw = '{"status": "PASS", "summary": "Looks good.", "risk_level": "Low", "anomalies": []}'
        parsed = LLMJSONParser.parse_response(raw)
        self.assertEqual(parsed["status"], "PASS")
        self.assertEqual(parsed["risk_level"], "Low")
        
    def test_markdown_wrapped_json(self):
        """Test parsing when LLM hallucinates markdown wrappers"""
        raw = '''Here is your result:
```json
{
  "status": "WARN",
  "summary": "Needs some work.",
  "risk_level": "Medium",
  "anomalies": ["Missing tests"]
}
```
Hope this helps!'''
        parsed = LLMJSONParser.parse_response(raw)
        self.assertEqual(parsed["status"], "WARN")
        self.assertEqual(parsed["anomalies"][0], "Missing tests")
        
    def test_invalid_enum_fallback(self):
        """Test parsing when LLM returns invalid enums"""
        raw = '{"status": "AWESOME", "summary": "Great", "risk_level": "Super High", "anomalies": []}'
        parsed = LLMJSONParser.parse_response(raw)
        
        # Should fallback to safe defaults
        self.assertEqual(parsed["status"], "WARN")
        self.assertEqual(parsed["risk_level"], "Medium")
        self.assertTrue(any("Invalid status" in a for a in parsed["anomalies"]))
        
    def test_complete_garbage_input(self):
        """Test parsing when LLM completely fails to return JSON"""
        raw = "I am an AI and I refuse to answer."
        parsed = LLMJSONParser.parse_response(raw)
        
        self.assertEqual(parsed["status"], "WARN")
        self.assertIn("System Error", parsed["anomalies"][0])
        
if __name__ == '__main__':
    unittest.main()
