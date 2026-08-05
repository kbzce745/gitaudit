# [STUDENT-WRITTEN]
import re

def parse_commit_diff(gitlab_diff_list):
    """
    Parse a list of diff objects from GitLab API into a structured feature dictionary.
    
    Extracts:
    - files_changed: List of unique file paths modified.
    - lines_added: Number of lines added (excluding +++ headers).
    - lines_deleted: Number of lines deleted (excluding --- headers).
    - modified_functions: Set of function/class names modified (Python, JS/TS, Java).
    - is_boilerplate_only: Boolean flag if changes are only boilerplate/locks/migrations.
    """
    files_changed = []
    lines_added = 0
    lines_deleted = 0
    modified_functions = set()
    
    # Regex patterns for function/class signatures in common languages
    # Python
    py_pattern = re.compile(r'^[+-]\s*(?:async\s+)?(?:def|class)\s+([a-zA-Z0-9_]+)')
    
    # JS/TS (function or class)
    js_pattern1 = re.compile(r'^[+-]\s*(?:export\s+)?(?:default\s+)?(?:function|class)\s+([a-zA-Z0-9_]+)')
    # JS/TS (arrow functions)
    js_pattern2 = re.compile(r'^[+-]\s*(?:export\s+)?(?:const|let|var)\s+([a-zA-Z0-9_]+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[a-zA-Z0-9_]+)\s*=>')
    
    # Java
    java_pattern = re.compile(r'^[+-]\s*(?:public|private|protected)?\s*(?:static)?\s*(?:class|interface|enum|[\w<>\[\]]+\s+)([a-zA-Z0-9_]+)\s*\(')

    for diff_obj in gitlab_diff_list:
        new_path = diff_obj.get("new_path")
        old_path = diff_obj.get("old_path")
        
        # Track changed files
        if new_path and new_path not in files_changed:
            files_changed.append(new_path)
        if old_path and old_path != new_path and old_path not in files_changed:
            files_changed.append(old_path)
            
        diff_text = diff_obj.get("diff", "")
        if not diff_text:
            continue
            
        lines = diff_text.split('\n')
        for line in lines:
            if line.startswith('+++') or line.startswith('---'):
                continue
            
            if line.startswith('+'):
                lines_added += 1
            elif line.startswith('-'):
                lines_deleted += 1
                
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

    # Determine if boilerplate
    # Patterns: package-lock.json, poetry.lock, yarn.lock, *.svg, Django migrations
    is_boilerplate_only = False
    if files_changed:
        boilerplate_pattern = re.compile(r'(package-lock\.json|poetry\.lock|yarn\.lock|\.svg$|migrations/.*\.py$)')
        is_boilerplate_only = all(boilerplate_pattern.search(f) for f in files_changed)
        
    return {
        "files_changed": files_changed,
        "lines_added": lines_added,
        "lines_deleted": lines_deleted,
        "modified_functions": list(modified_functions),
        "is_boilerplate_only": is_boilerplate_only
    }
