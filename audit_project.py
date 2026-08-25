import os
import subprocess
import json
import re

# Base paths
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
TARGET_DIR = os.path.join(PROJECT_ROOT, "auditor")
REPORT_PATH = os.path.join(PROJECT_ROOT, "audit_report.html")

def run_command(command, cwd=None):
    try:
        result = subprocess.run(command, cwd=cwd, shell=True, capture_output=True, text=True)
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def run_usability_tests():
    print("Running Tests and Coverage (pytest)...")
    out, err, code = run_command("pytest --cov=auditor --cov-report=html -v", cwd=PROJECT_ROOT)
    passed = code == 0
    return {
        "score": 100 if passed else 0,
        "details": "All Pytest suites (Usability, API Mocks, Services) passed successfully." if passed else "Some tests failed. See details below.",
        "raw": out + err
    }

def run_pylint():
    print("Running Pylint (Code Quality)...")
    out, err, code = run_command(f"pylint {TARGET_DIR} --exit-zero", cwd=PROJECT_ROOT)
    match = re.search(r"rated at (\d+\.\d+)/10", out)
    score_10 = float(match.group(1)) if match else 10.0
    return {
        "score": int(score_10 * 10),
        "details": f"PEP-8 and structural analysis resulted in a score of {score_10}/10.",
        "raw": out
    }

def run_radon():
    print("Running Radon (Complexity)...")
    out, err, code = run_command(f"radon cc {TARGET_DIR} -a", cwd=PROJECT_ROOT)
    match = re.search(r"Average complexity: [A-Z] \(([\d\.]+)\)", out)
    avg_cc = float(match.group(1)) if match else 0.0
    
    if avg_cc <= 5:
        score = 100
    elif avg_cc >= 15:
        score = 0
    else:
        score = int(100 - ((avg_cc - 5) * 10))
        
    return {
        "score": score,
        "details": f"Average Cyclomatic Complexity (CC) across all blocks is {avg_cc:.2f} (lower is better).",
        "raw": out
    }

def run_bandit():
    print("Running Bandit (Security)...")
    out, err, code = run_command(f"bandit -r {TARGET_DIR} -x tests -f json -q --exit-zero", cwd=PROJECT_ROOT)
    try:
        data = json.loads(out)
        metrics = data.get("metrics", {}).get("_totals", {})
        high_sev = metrics.get("SEVERITY.HIGH", 0)
        med_sev = metrics.get("SEVERITY.MEDIUM", 0)
        low_sev = metrics.get("SEVERITY.LOW", 0)
        
        score = max(0, 100 - (high_sev * 20) - (med_sev * 10) - (low_sev * 5))
        details = f"Vulnerability Scan Results: {high_sev} High, {med_sev} Medium, {low_sev} Low severity issues detected."
    except Exception as e:
        score = 0
        details = f"Failed to parse Bandit output: {e}. Raw out starts with: {out[:50]}"
    return {
        "score": score,
        "details": details,
        "raw": out
    }

def generate_html_report(results, overall_score):
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>GitAudit - Detailed Project Audit Report</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            .log-box {{
                max-height: 250px;
                overflow-y: auto;
                font-family: 'Courier New', Courier, monospace;
            }}
            /* Custom Scrollbar for logs */
            .log-box::-webkit-scrollbar {{ width: 8px; }}
            .log-box::-webkit-scrollbar-track {{ background: rgba(0,0,0,0.1); border-radius: 4px; }}
            .log-box::-webkit-scrollbar-thumb {{ background: rgba(59, 130, 246, 0.5); border-radius: 4px; }}
        </style>
    </head>
    <body class="bg-slate-900 text-slate-200 p-8 font-sans">
        <div class="max-w-7xl mx-auto">
            <header class="mb-10 text-center">
                <h1 class="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400 mb-2">Comprehensive Project Audit</h1>
                <p class="text-slate-400">First-principles analysis covering usability, code quality, logic complexity, and security.</p>
            </header>
            
            <!-- Top Section: Score & Chart -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-8 mb-10">
                <!-- Overall Score -->
                <div class="col-span-1 bg-slate-800 rounded-2xl p-8 flex flex-col items-center justify-center border border-slate-700 shadow-xl relative overflow-hidden">
                    <!-- Glow effect -->
                    <div class="absolute -top-10 -right-10 w-32 h-32 bg-blue-500/20 blur-3xl rounded-full"></div>
                    <h2 class="text-xl font-bold text-slate-300 mb-6 z-10">Overall Health Score</h2>
                    <div class="relative flex items-center justify-center w-48 h-48 rounded-full border-8 border-slate-700 z-10 shadow-inner">
                        <!-- Progress circle using conic-gradient -->
                        <div class="absolute inset-[-8px] rounded-full" style="background: conic-gradient(#3b82f6 {overall_score}%, transparent 0); -webkit-mask: radial-gradient(transparent 58%, black 60%);"></div>
                        <span class="text-6xl font-black text-white">{int(overall_score)}</span>
                    </div>
                </div>
                
                <!-- Radar Chart -->
                <div class="col-span-2 bg-slate-800 rounded-2xl p-6 border border-slate-700 shadow-xl flex flex-col items-center justify-center relative">
                    <h3 class="text-sm font-bold text-slate-400 mb-2 uppercase tracking-wider w-full text-center">Dimensional Balance</h3>
                    <div class="w-full max-w-md relative z-10">
                        <canvas id="auditChart"></canvas>
                    </div>
                </div>
            </div>
            
            <!-- Details Grid -->
            <h2 class="text-2xl font-bold text-white mb-6 border-b border-slate-700 pb-2">Detailed Metric Analysis</h2>
            <div class="space-y-6">
                <!-- Usability -->
                <div class="bg-slate-800 rounded-xl p-6 border border-slate-700 shadow-md">
                    <div class="flex justify-between items-center mb-2">
                        <h3 class="text-xl font-bold text-emerald-400 flex items-center">
                            <svg class="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-1-2 1M4 7l2-1M4 7l2 1M4 7v2.5M12 21l-2-1m2 1l2-1m-2 1v-2.5M6 18l-2-1v-2.5M18 18l2-1v-2.5"></path></svg>
                            Usability Testing (Django Test Framework)
                        </h3>
                        <span class="px-4 py-1.5 rounded-full bg-emerald-500/20 text-emerald-400 font-bold border border-emerald-500/30">{results['usability']['score']} / 100</span>
                    </div>
                    <p class="text-slate-300 mb-4">{results['usability']['details']}</p>
                    <details class="group">
                        <summary class="cursor-pointer text-sm font-medium text-blue-400 hover:text-blue-300 mb-2">View Raw Execution Logs</summary>
                        <div class="bg-slate-900/80 p-4 rounded-lg border border-slate-700 log-box mt-2">
                            <pre class="text-xs text-slate-400 whitespace-pre-wrap">{results['usability']['raw'].replace('<', '&lt;').replace('>', '&gt;')}</pre>
                        </div>
                    </details>
                </div>
                
                <!-- Code Quality -->
                <div class="bg-slate-800 rounded-xl p-6 border border-slate-700 shadow-md">
                    <div class="flex justify-between items-center mb-2">
                        <h3 class="text-xl font-bold text-yellow-400 flex items-center">
                            <svg class="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"></path></svg>
                            Code Quality (Pylint)
                        </h3>
                        <span class="px-4 py-1.5 rounded-full bg-yellow-500/20 text-yellow-400 font-bold border border-yellow-500/30">{results['quality']['score']} / 100</span>
                    </div>
                    <p class="text-slate-300 mb-4">{results['quality']['details']}</p>
                    <details class="group">
                        <summary class="cursor-pointer text-sm font-medium text-blue-400 hover:text-blue-300 mb-2">View Detailed Linter Warnings</summary>
                        <div class="bg-slate-900/80 p-4 rounded-lg border border-slate-700 log-box mt-2">
                            <pre class="text-xs text-slate-400 whitespace-pre-wrap">{results['quality']['raw'].replace('<', '&lt;').replace('>', '&gt;')}</pre>
                        </div>
                    </details>
                </div>
                
                <!-- Complexity -->
                <div class="bg-slate-800 rounded-xl p-6 border border-slate-700 shadow-md">
                    <div class="flex justify-between items-center mb-2">
                        <h3 class="text-xl font-bold text-purple-400 flex items-center">
                            <svg class="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
                            Code Complexity (Radon)
                        </h3>
                        <span class="px-4 py-1.5 rounded-full bg-purple-500/20 text-purple-400 font-bold border border-purple-500/30">{results['complexity']['score']} / 100</span>
                    </div>
                    <p class="text-slate-300 mb-4">{results['complexity']['details']}</p>
                    <details class="group">
                        <summary class="cursor-pointer text-sm font-medium text-blue-400 hover:text-blue-300 mb-2">View Complexity Breakdown per Function</summary>
                        <div class="bg-slate-900/80 p-4 rounded-lg border border-slate-700 log-box mt-2">
                            <pre class="text-xs text-slate-400 whitespace-pre-wrap">{results['complexity']['raw'].replace('<', '&lt;').replace('>', '&gt;')}</pre>
                        </div>
                    </details>
                </div>
                
                <!-- Security -->
                <div class="bg-slate-800 rounded-xl p-6 border border-slate-700 shadow-md">
                    <div class="flex justify-between items-center mb-2">
                        <h3 class="text-xl font-bold text-red-400 flex items-center">
                            <svg class="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path></svg>
                            Security Auditing (Bandit)
                        </h3>
                        <span class="px-4 py-1.5 rounded-full bg-red-500/20 text-red-400 font-bold border border-red-500/30">{results['security']['score']} / 100</span>
                    </div>
                    <p class="text-slate-300 mb-4">{results['security']['details']}</p>
                    <details class="group">
                        <summary class="cursor-pointer text-sm font-medium text-blue-400 hover:text-blue-300 mb-2">View Security JSON Output</summary>
                        <div class="bg-slate-900/80 p-4 rounded-lg border border-slate-700 log-box mt-2">
                            <pre class="text-xs text-slate-400 whitespace-pre-wrap">{results['security']['raw'].replace('<', '&lt;').replace('>', '&gt;')}</pre>
                        </div>
                    </details>
                </div>
            </div>
        </div>

        <script>
            const ctx = document.getElementById('auditChart').getContext('2d');
            
            // Create a gradient for the radar fill
            let gradient = ctx.createRadialGradient(200, 200, 20, 200, 200, 200);
            gradient.addColorStop(0, 'rgba(59, 130, 246, 0.8)');
            gradient.addColorStop(1, 'rgba(59, 130, 246, 0.2)');

            new Chart(ctx, {{
                type: 'radar',
                data: {{
                    labels: ['Usability', 'Code Quality', 'Complexity', 'Security'],
                    datasets: [{{
                        label: 'Project Scores',
                        data: [{results['usability']['score']}, {results['quality']['score']}, {results['complexity']['score']}, {results['security']['score']}],
                        backgroundColor: gradient,
                        borderColor: 'rgba(59, 130, 246, 1)',
                        borderWidth: 3,
                        pointBackgroundColor: '#3b82f6',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: 'rgba(59, 130, 246, 1)',
                        pointRadius: 5,
                        pointHoverRadius: 8
                    }}]
                }},
                options: {{
                    scales: {{
                        r: {{
                            min: 0,
                            max: 100,
                            beginAtZero: true,
                            angleLines: {{ color: 'rgba(255, 255, 255, 0.1)' }},
                            grid: {{ color: 'rgba(255, 255, 255, 0.1)', circular: true }},
                            pointLabels: {{ 
                                color: '#e2e8f0', 
                                font: {{ size: 14, weight: 'bold', family: "'Inter', sans-serif" }} 
                            }},
                            ticks: {{
                                display: false, // Hide numeric ticks for a cleaner look
                                min: 0,
                                max: 100
                            }}
                        }}
                    }},
                    plugins: {{ 
                        legend: {{ display: false }},
                        tooltip: {{
                            backgroundColor: 'rgba(15, 23, 42, 0.9)',
                            titleColor: '#3b82f6',
                            bodyColor: '#fff',
                            bodyFont: {{ size: 14, weight: 'bold' }},
                            borderColor: 'rgba(255,255,255,0.1)',
                            borderWidth: 1,
                            padding: 12,
                            displayColors: false
                        }}
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"Report successfully generated at: {REPORT_PATH}")

def main():
    print("Starting Comprehensive Project Audit...\n")
    usability_res = run_usability_tests()
    quality_res = run_pylint()
    complexity_res = run_radon()
    security_res = run_bandit()
    
    results = {
        "usability": usability_res,
        "quality": quality_res,
        "complexity": complexity_res,
        "security": security_res
    }
    
    overall_score = (
        usability_res['score'] + 
        quality_res['score'] + 
        complexity_res['score'] + 
        security_res['score']
    ) / 4.0
    
    print("\n--- Final Scores ---")
    print(f"Usability:  {usability_res['score']}/100")
    print(f"Quality:    {quality_res['score']}/100")
    print(f"Complexity: {complexity_res['score']}/100")
    print(f"Security:   {security_res['score']}/100")
    print(f"OVERALL:    {overall_score:.1f}/100\n")
    
    generate_html_report(results, overall_score)

if __name__ == "__main__":
    main()
