#!/usr/bin/env python3
"""
Security Validation Script
Checks for common security issues in the project.
"""

import os
import re
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict, Optional

class SecurityValidator:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.issues = []
        self.warnings = []
        
    def log_issue(self, severity: str, message: str, file_path: Optional[str] = None):
        """Log a security issue"""
        entry = {
            'severity': severity,
            'message': message,
            'file': file_path
        }
        if severity == 'ERROR':
            self.issues.append(entry)
        else:
            self.warnings.append(entry)
    
    def check_env_files(self):
        """Check for .env file security issues"""
        print("🔍 Checking environment files...")
        
        # Check if .env exists and has real secrets
        env_file = self.project_root / '.env'
        if env_file.exists():
            content = env_file.read_text()
            
            # Look for patterns that indicate real secrets
            secret_patterns = [
                r'[A-Za-z0-9+/]{32,}={0,2}',  # Base64 encoded secrets
                r'[0-9a-fA-F]{32}',           # 32-char hex keys
                r'sk-[a-zA-Z0-9]{32,}',       # OpenAI-style keys
                r'AKIA[0-9A-Z]{16}',          # AWS access keys
            ]
            
            for line_num, line in enumerate(content.split('\n'), 1):
                for pattern in secret_patterns:
                    if re.search(pattern, line) and not line.strip().startswith('#'):
                        if 'your-' not in line.lower() and 'placeholder' not in line.lower():
                            self.log_issue('ERROR', 
                                f'Potential real secret detected on line {line_num}', 
                                str(env_file))
        
        # Check if .env.example exists
        env_example = self.project_root / '.env.example'
        if not env_example.exists():
            self.log_issue('WARNING', 
                'Missing .env.example template file', 
                str(env_example))
    
    def check_gitignore(self):
        """Check .gitignore configuration"""
        print("🔍 Checking .gitignore configuration...")
        
        gitignore_file = self.project_root / '.gitignore'
        if not gitignore_file.exists():
            self.log_issue('ERROR', 'Missing .gitignore file')
            return
        
        content = gitignore_file.read_text()
        required_patterns = ['.env', '*.key', '*.pem', 'credentials.json']
        
        for pattern in required_patterns:
            if pattern not in content:
                self.log_issue('WARNING', 
                    f'Missing {pattern} in .gitignore', 
                    str(gitignore_file))
    
    def check_git_tracking(self):
        """Check if sensitive files are tracked by git"""
        print("🔍 Checking git tracking...")
        
        try:
            # Check if .env is tracked
            result = subprocess.run(
                ['git', 'ls-files', '.env'], 
                cwd=self.project_root, 
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                self.log_issue('ERROR', 
                    '.env file is tracked by git - this is a security risk!')
            
            # Check for other sensitive files
            sensitive_patterns = ['*.key', '*.pem', 'credentials.json']
            for pattern in sensitive_patterns:
                result = subprocess.run(
                    ['git', 'ls-files', pattern], 
                    cwd=self.project_root, 
                    capture_output=True, 
                    text=True
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    files = result.stdout.strip().split('\n')
                    for file in files:
                        self.log_issue('ERROR', 
                            f'Sensitive file {file} is tracked by git')
                            
        except subprocess.SubprocessError:
            self.log_issue('WARNING', 'Could not check git status (not a git repository?)')
    
    def check_source_code(self):
        """Check source code for hardcoded secrets"""
        print("🔍 Scanning source code for hardcoded secrets...")
        
        # Patterns that might indicate hardcoded secrets
        secret_patterns = [
            (r'api[_-]?key\s*=\s*["\'][^"\']{10,}["\']', 'API key'),
            (r'secret\s*=\s*["\'][^"\']{10,}["\']', 'Secret'),
            (r'password\s*=\s*["\'][^"\']{6,}["\']', 'Password'),
            (r'token\s*=\s*["\'][^"\']{10,}["\']', 'Token'),
            (r'["\'][0-9a-fA-F]{32}["\']', '32-character hex string'),
            (r'["\'][A-Za-z0-9+/]{40,}={0,2}["\']', 'Base64 encoded data'),
        ]
        
        # Files to check
        code_extensions = ['.py', '.js', '.ts', '.java', '.cs', '.go', '.rs']
        
        for file_path in self.project_root.rglob('*'):
            if (file_path.is_file() and 
                file_path.suffix in code_extensions and
                '.git' not in str(file_path) and
                '__pycache__' not in str(file_path)):
                
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    
                    for line_num, line in enumerate(content.split('\n'), 1):
                        # Skip comments and example files
                        if (line.strip().startswith('#') or 
                            line.strip().startswith('//') or
                            'example' in str(file_path).lower() or
                            'demo' in str(file_path).lower()):
                            continue
                        
                        for pattern, desc in secret_patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                # Additional checks to reduce false positives
                                if ('your-' not in line.lower() and 
                                    'placeholder' not in line.lower() and
                                    'example' not in line.lower() and
                                    'dummy' not in line.lower() and
                                    'test' not in line.lower()):
                                    
                                    self.log_issue('WARNING', 
                                        f'Potential {desc} on line {line_num}: {line.strip()[:50]}...', 
                                        str(file_path))
                
                except Exception as e:
                    self.log_issue('WARNING', 
                        f'Could not read file: {e}', 
                        str(file_path))
    
    def check_container_security(self):
        """Check Docker files for security issues"""
        print("🔍 Checking container security...")
        
        docker_files = list(self.project_root.rglob('Dockerfile*'))
        docker_files.extend(list(self.project_root.rglob('docker-compose*.yml')))
        
        for file_path in docker_files:
            try:
                content = file_path.read_text()
                
                # Check for hardcoded secrets in Docker files
                secret_patterns = [
                    r'ENV\s+.*[A-Za-z0-9+/]{32,}',
                    r'ARG\s+.*[A-Za-z0-9+/]{32,}',
                ]
                
                for line_num, line in enumerate(content.split('\n'), 1):
                    for pattern in secret_patterns:
                        if re.search(pattern, line):
                            if ('your-' not in line.lower() and 
                                'placeholder' not in line.lower()):
                                self.log_issue('WARNING', 
                                    f'Potential secret in Docker file on line {line_num}', 
                                    str(file_path))
                
            except Exception as e:
                self.log_issue('WARNING', 
                    f'Could not read Docker file: {e}', 
                    str(file_path))
    
    def generate_report(self):
        """Generate security report"""
        print("\n" + "="*60)
        print("🔒 SECURITY VALIDATION REPORT")
        print("="*60)
        
        if not self.issues and not self.warnings:
            print("✅ No security issues found!")
            return True
        
        if self.issues:
            print(f"\n🚨 CRITICAL ISSUES ({len(self.issues)}):")
            for issue in self.issues:
                print(f"   ❌ {issue['message']}")
                if issue['file']:
                    print(f"      📁 {issue['file']}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   🔸 {warning['message']}")
                if warning['file']:
                    print(f"      📁 {warning['file']}")
        
        print("\n" + "="*60)
        
        if self.issues:
            print("🚨 SECURITY ISSUES FOUND - Please fix before deployment!")
            return False
        else:
            print("✅ No critical security issues found.")
            if self.warnings:
                print("⚠️  Please review warnings above.")
            return True

def main():
    """Main function"""
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    print("🔒 Security Validation Script")
    print(f"📁 Project: {project_root}")
    print("-" * 60)
    
    validator = SecurityValidator(project_root)
    
    # Run all checks
    validator.check_env_files()
    validator.check_gitignore()
    validator.check_git_tracking()
    validator.check_source_code()
    validator.check_container_security()
    
    # Generate report
    success = validator.generate_report()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
