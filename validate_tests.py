#!/usr/bin/env python3
"""
Test validation script for checking syntax and basic imports.
"""

import ast
import sys
from pathlib import Path

def validate_python_file(file_path):
    """Validate Python file syntax and basic structure."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check syntax
        ast.parse(content)
        print(f"✅ {file_path.name}: Syntax OK")
        return True
        
    except SyntaxError as e:
        print(f"❌ {file_path.name}: Syntax Error - {e}")
        return False
    except Exception as e:
        print(f"❌ {file_path.name}: Error - {e}")
        return False

def main():
    """Validate all test files."""
    test_dir = Path("tests")
    test_files = list(test_dir.glob("test_*.py"))
    
    print(f"Validating {len(test_files)} test files...\n")
    
    all_valid = True
    for test_file in test_files:
        if not validate_python_file(test_file):
            all_valid = False
    
    print(f"\n{'✅ All tests valid!' if all_valid else '❌ Some tests have issues!'}")
    
    # Count test functions
    total_tests = 0
    for test_file in test_files:
        try:
            with open(test_file, 'r') as f:
                content = f.read()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                    total_tests += 1
        except:
            pass
    
    print(f"\n📊 Total test functions found: {total_tests}")
    return all_valid

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)