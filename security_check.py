#!/usr/bin/env python3
"""
🔒 Security Verification Script
Checks for hardcoded API keys and sensitive information before Git push
"""

import os
import re
import glob

def scan_for_api_keys():
    """Scan all Python files for potential hardcoded API keys"""
    
    # Patterns to look for
    api_key_patterns = [
        r'api_key\s*=\s*["\'][A-Za-z0-9_-]{20,}["\']',
        r'API_KEY\s*=\s*["\'][A-Za-z0-9_-]{20,}["\']',
        r'AIzaSy[A-Za-z0-9_-]{33}',  # Google API keys
        r'sk-[A-Za-z0-9]{48}',       # OpenAI API keys
        r'xoxb-[A-Za-z0-9-]{50,}',   # Slack tokens
    ]
    
    # Files to scan
    python_files = glob.glob("**/*.py", recursive=True)
    
    issues_found = []
    
    for file_path in python_files:
        if "fraud_env" in file_path or "__pycache__" in file_path:
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for line_num, line in enumerate(content.split('\n'), 1):
                for pattern in api_key_patterns:
                    if re.search(pattern, line):
                        issues_found.append({
                            'file': file_path,
                            'line': line_num,
                            'content': line.strip(),
                            'pattern': pattern
                        })
        except Exception as e:
            print(f"⚠️ Could not scan {file_path}: {e}")
    
    return issues_found

def main():
    print("🔒 Security Scan: Checking for hardcoded API keys...")
    print("=" * 60)
    
    issues = scan_for_api_keys()
    
    if issues:
        print(f"🚨 SECURITY ALERT: Found {len(issues)} potential issues:")
        print()
        
        for issue in issues:
            print(f"📁 File: {issue['file']}")
            print(f"📍 Line {issue['line']}: {issue['content']}")
            print(f"🔍 Pattern: {issue['pattern']}")
            print("-" * 40)
        
        print()
        print("🛡️ ACTIONS NEEDED:")
        print("1. Move API keys to .env file")
        print("2. Use os.getenv() to load from environment")
        print("3. Add .env to .gitignore")
        print("4. Re-run this script to verify fixes")
        
        return False
    else:
        print("✅ Security scan passed!")
        print("🔒 No hardcoded API keys found")
        print("✨ Safe to push to GitHub")
        
        # Check if .env is in .gitignore
        try:
            with open('.gitignore', 'r') as f:
                gitignore_content = f.read()
                if '.env' in gitignore_content:
                    print("✅ .env file is properly ignored by Git")
                else:
                    print("⚠️ Add .env to .gitignore file")
        except FileNotFoundError:
            print("⚠️ Create .gitignore file and add .env")
        
        return True

if __name__ == "__main__":
    main()
