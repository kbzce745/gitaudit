import os
import sys
import unittest

# 动态添加项目根目录到 sys.path，让测试脚本能找到 auditor 包
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from auditor.diff_parser import parse_commit_diff

class TestDiffParser(unittest.TestCase):

    def test_basic_stats(self):
        """Difference Report: List of modified files, number of lines added, number of lines deleted"""
        mock_diff = [{
            "new_path": "src/main.py",
            "old_path": "src/main.py",
            "diff": "@@ -1,3 +1,4 @@\n import os\n+import sys\n-print('hello')\n+print('world')\n+print('new line')"
        }]
        result = parse_commit_diff(mock_diff)
        
        self.assertEqual(result["files_changed"], ["src/main.py"])
        self.assertEqual(result["lines_added"], 3)
        self.assertEqual(result["lines_deleted"], 1)

    def test_function_extraction(self):
        """Test extraction of function/class signatures for Python, JS/TS, and Java"""
        mock_diff = [
            {
                "new_path": "app.py",
                "old_path": "app.py",
                "diff": "@@ -10,2 +10,2 @@\n+def test_python_func():\n+class MyPythonClass:\n"
            }, 
            {
                "new_path": "script.js",
                "old_path": "script.js",
                "diff": "@@ -5,2 +5,2 @@\n+export function myJsFunc() {\n+const myArrowFunc = () => {"
            }, 
            {
                "new_path": "Main.java",
                "old_path": "Main.java",
                "diff": "@@ -1,2 +1,2 @@\n+public static void main(String[] args) {\n+private class MyJavaClass {"
            }
        ]
        
        result = parse_commit_diff(mock_diff)
        funcs = result["modified_functions"]
        
        # Verification
        self.assertIn("test_python_func", funcs)
        self.assertIn("MyPythonClass", funcs)
        self.assertIn("myJsFunc", funcs)
        self.assertIn("myArrowFunc", funcs)
        self.assertIn("main", funcs)
        self.assertIn("MyJavaClass", funcs)

    def test_boilerplate_detection(self):
        """Test automatic identification of pure scaffold/generated boilerplate commits"""
        # Test scenario 1: All lock files and database migration scripts
        mock_diff_boilerplate = [
            {"new_path": "package-lock.json", "old_path": "package-lock.json", "diff": "+version: 1"},
            {"new_path": "auditor/migrations/0002_auto.py", "old_path": "auditor/migrations/0002_auto.py", "diff": "+class Migration:"}
        ]
        result_boilerplate = parse_commit_diff(mock_diff_boilerplate)
        self.assertTrue(result_boilerplate["is_boilerplate_only"])

        # Test scenario 2: Contains both lock files and actual business code logic modifications
        mock_diff_mixed = mock_diff_boilerplate + [
            {"new_path": "auditor/models.py", "old_path": "auditor/models.py", "diff": "+class NewModel:"}
        ]
        result_mixed = parse_commit_diff(mock_diff_mixed)
        self.assertFalse(result_mixed["is_boilerplate_only"])

    def test_tier1_metrics(self):
        """Test Tier 1 metrics: LOC, CDR, TSR, Gini, and Anomalies"""
        mock_diff = [
            {
                "new_path": "src/main.py",
                "old_path": "src/main.py",
                "diff": "+import sys\n-import os" # 1 added, 1 deleted -> loc 2
            },
            {
                "new_path": "tests/test_main.py",
                "old_path": "tests/test_main.py",
                "diff": "+def test_sys():\n+    pass\n+    pass\n+    pass" # 4 added -> loc 4
            }
        ]
        
        result = parse_commit_diff(mock_diff)
        
        self.assertEqual(result["total_loc"], 6)
        
        # CDR = lines_deleted (1) / total_loc (6) = 0.1667
        self.assertEqual(result["cdr"], 0.1667)
        
        # TSR = test_loc (4) / total_loc (6) = 0.6667
        self.assertEqual(result["tsr"], 0.6667)
        
        # Gini for [2, 4]: 
        # Mean = 3. 
        # sum(|xi-xj|) = |2-2| + |2-4| + |4-2| + |4-4| = 4
        # G = 4 / (2 * 2^2 * 3) = 4 / 24 = 0.1667
        self.assertEqual(result["gini_loc"], 0.1667)
        self.assertFalse(result["is_anomaly"])

    def test_anomalies(self):
        """Test LOC > 1000 and Gini > 0.8 anomaly detection"""
        # Test LOC anomaly
        mock_diff_loc = [{"new_path": "data.txt", "old_path": "data.txt", "diff": "+line\n" * 1501}]
        res1 = parse_commit_diff(mock_diff_loc)
        self.assertTrue(res1["is_anomaly"])
        self.assertIn("LOC > 1000", res1["anomaly_reason"][0])
        
        # Test Gini anomaly
        # 1 file with 100 changes, 9 files with 1 change -> highly concentrated
        mock_diff_gini = [{"new_path": "core.py", "old_path": "core.py", "diff": "+line\n" * 100}]
        for i in range(9):
            mock_diff_gini.append({"new_path": f"file{i}.txt", "old_path": f"file{i}.txt", "diff": "+line\n"})
        
        res2 = parse_commit_diff(mock_diff_gini)
        self.assertTrue(res2["is_anomaly"])
        self.assertTrue(any("Gini > 0.8" in reason for reason in res2["anomaly_reason"]))

if __name__ == '__main__':
    unittest.main()
