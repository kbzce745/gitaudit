# [STUDENT-WRITTEN]
import re

def calculate_gini(values):
    """
    Calculate the Gini coefficient of a list of numeric values.
    Returns a value between 0.0 and 1.0.
    """
    if not values:
        return 0.0
    values = sorted(values)
    n = len(values)
    mean_val = sum(values) / n
    if mean_val == 0:
        return 0.0
    
    # Gini index formula: G = sum( (2i - n - 1) * x_i ) / (n * sum(x_i))
    gini = sum((2 * (i + 1) - n - 1) * v for i, v in enumerate(values)) / (n * sum(values))
    return round(gini, 4)

def parse_commit_diff(gitlab_diff_list):
    """
    Parse a list of diff objects from GitLab API into a structured feature dictionary
    compliant with Tier 1 analytical requirements.
    """
    files_changed = []
    lines_added = 0
    lines_deleted = 0
    modified_functions = set()
    loc_per_file = {}
    
    # Regex patterns for function/class signatures in common languages
    py_pattern = re.compile(r'^[+-]\s*(?:async\s+)?(?:def|class)\s+([a-zA-Z0-9_]+)')
    js_pattern1 = re.compile(r'^[+-]\s*(?:export\s+)?(?:default\s+)?(?:function|class)\s+([a-zA-Z0-9_]+)')
    js_pattern2 = re.compile(r'^[+-]\s*(?:export\s+)?(?:const|let|var)\s+([a-zA-Z0-9_]+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[a-zA-Z0-9_]+)\s*=>')
    java_pattern = re.compile(r'^[+-]\s*(?:public|private|protected)?\s*(?:static)?\s*(?:class|interface|enum|[\w<>\[\]]+\s+)([a-zA-Z0-9_]+)(?:\s*\(|\s*\{|\s+)')

    for diff_obj in gitlab_diff_list:
        new_path = diff_obj.get("new_path")
        old_path = diff_obj.get("old_path")
        filepath = new_path or old_path
        
        # Track changed files
        if new_path and new_path not in files_changed:
            files_changed.append(new_path)
        if old_path and old_path != new_path and old_path not in files_changed:
            files_changed.append(old_path)
            
        diff_text = diff_obj.get("diff", "")
        if not diff_text:
            continue
            
        file_loc = 0
        lines = diff_text.split('\n')
        for line in lines:
            if line.startswith('+++') or line.startswith('---'):
                continue
            
            if line.startswith('+'):
                lines_added += 1
                file_loc += 1
            elif line.startswith('-'):
                lines_deleted += 1
                file_loc += 1
                
            # Extract function/class signatures on added/removed lines
            if line.startswith('+') or line.startswith('-'):
                if match := py_pattern.search(line):
                    modified_functions.add(match.group(1))
                elif match := js_pattern1.search(line):
                    modified_functions.add(match.group(1))
                elif match := js_pattern2.search(line):
                    modified_functions.add(match.group(1))
                elif match := java_pattern.search(line):
                    modified_functions.add(match.group(1))

        if filepath:
            loc_per_file[filepath] = loc_per_file.get(filepath, 0) + file_loc

    # Determine if boilerplate
    is_boilerplate_only = False
    if files_changed:
        boilerplate_pattern = re.compile(r'(package-lock\.json|poetry\.lock|yarn\.lock|\.svg$|migrations/.*\.py$)')
        is_boilerplate_only = all(boilerplate_pattern.search(f) for f in files_changed)

    # --- Tier 1 Mathematics ---
    
    # LOC
    total_loc = lines_added + lines_deleted
    
    # CDR (Code Deletion Ratio)
    cdr = round(lines_deleted / total_loc, 4) if total_loc > 0 else 0.0
    
    # TSR (Test to Source Ratio)
    test_loc = sum(loc for path, loc in loc_per_file.items() if re.search(r'(test|spec|mock)', path, re.IGNORECASE))
    tsr = round(test_loc / total_loc, 4) if total_loc > 0 else 0.0
    
    # Gini Coefficient (G_LOC)
    gini_loc = calculate_gini(list(loc_per_file.values()))
    
    # Burstiness (B) - Evaluated on a weekly historical basis.
    # Currently acting as a reserved placeholder in the payload (0.0).
    burstiness = 0.0
    
    # Anomaly Detection
    is_anomaly = False
    anomaly_reason = []
    
    if total_loc > 1500:
        is_anomaly = True
        anomaly_reason.append(f"LOC > 1500 (Current: {total_loc})")
        
    if gini_loc > 0.8 and total_loc > 50:
        is_anomaly = True
        anomaly_reason.append(f"Gini > 0.8 (Highly concentrated changes, G_LOC: {gini_loc})")
        
    return {
        "files_changed": files_changed,
        "lines_added": lines_added,
        "lines_deleted": lines_deleted,
        "total_loc": total_loc,
        "cdr": cdr,
        "tsr": tsr,
        "gini_loc": gini_loc,
        "burstiness": burstiness,
        "is_anomaly": is_anomaly,
        "anomaly_reason": anomaly_reason,
        "modified_functions": list(modified_functions),
        "is_boilerplate_only": is_boilerplate_only
    }
