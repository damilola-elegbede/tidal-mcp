#!/usr/bin/env python3
"""
Security validation script for test infrastructure.
"""

import re
import sys
from pathlib import Path
from typing import Any


class SecurityValidator:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.issues = []
        self.passed_checks = []

    def scan_hardcoded_credentials(self) -> None:
        """Scan for hardcoded credentials in test files."""
        test_files = list(self.project_root.glob("tests/**/*.py"))

        dangerous_patterns = [
            r'"test_client_secret"',
            r'"test_access_token"',
            r'redis://localhost:6379[^/]',
        ]

        for test_file in test_files:
            content = test_file.read_text()
            for pattern in dangerous_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    self.issues.append({
                        "type": "hardcoded_credential",
                        "file": str(test_file),
                        "matches": matches,
                        "severity": "CRITICAL"
                    })

        if not any(issue["type"] == "hardcoded_credential" for issue in self.issues):
            self.passed_checks.append("No hardcoded credentials found")

    def validate_fake_credentials(self) -> None:
        """Check credentials are marked as fake."""
        test_files = list(self.project_root.glob("tests/**/*.py"))

        for test_file in test_files:
            content = test_file.read_text()
            patterns = [
                r'client_secret.*=.*["\']([^"\']+)["\']',
                r'access_token.*=.*["\']([^"\']+)["\']',
            ]

            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Skip if it contains safety markers
                    if any(marker in match.lower() for marker in ['fake', 'test', 'never_real']):
                        continue
                    # Skip if it's a parameter name or placeholder
                    if match in ['param_client_secret', 'param_client_id', '{client_secret}', '{access_token}']:
                        continue
                    # Only flag if it looks like a real credential
                    if len(match) > 10 and not match.startswith('{{') and not match.endswith('}}'):
                        self.issues.append({
                            "type": "unsafe_credential",
                            "file": str(test_file),
                            "credential": match,
                            "severity": "HIGH"
                        })

        if not any(issue["type"] == "unsafe_credential" for issue in self.issues):
            self.passed_checks.append("All credentials properly marked as fake")

    def check_environment_isolation(self) -> None:
        """Check for environment isolation fixture."""
        conftest_files = list(self.project_root.glob("tests/**/conftest.py"))

        isolation_found = False
        for conftest_file in conftest_files:
            content = conftest_file.read_text()
            if "isolate_test_environment" in content and "autouse=True" in content:
                isolation_found = True
                break

        if not isolation_found:
            self.issues.append({
                "type": "missing_isolation",
                "severity": "HIGH",
                "description": "Missing environment isolation fixture"
            })
        else:
            self.passed_checks.append("Environment isolation fixture found")

    def run_validation(self) -> dict[str, Any]:
        """Run validation checks."""
        print("Running security validation...")

        self.scan_hardcoded_credentials()
        self.validate_fake_credentials()
        self.check_environment_isolation()

        return {
            "passed_checks": self.passed_checks,
            "issues": self.issues,
            "security_score": len(self.passed_checks) / (len(self.passed_checks) + len(self.issues)) * 100 if (len(self.passed_checks) + len(self.issues)) > 0 else 100
        }

def main():
    project_root = Path(__file__).parent.parent
    validator = SecurityValidator(project_root)
    results = validator.run_validation()

    print("\nSecurity Validation Results:")
    print(f"Checks passed: {len(results['passed_checks'])}")
    print(f"Issues found: {len(results['issues'])}")
    print(f"Security score: {results['security_score']:.1f}%")

    if results['passed_checks']:
        print("\nPassed checks:")
        for check in results['passed_checks']:
            print(f"  • {check}")

    if results['issues']:
        print("\nSecurity issues:")
        for issue in results['issues']:
            print(f"  {issue['severity']}: {issue['type']}")
            if 'file' in issue:
                print(f"    File: {issue['file']}")
            if 'matches' in issue:
                print(f"    Matches: {issue['matches']}")
            print()

    return len(results['issues'])

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
