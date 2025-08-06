#!/usr/bin/env python3
"""
Test Coverage Summary

Provides an overview of test coverage for the Tidal MCP project.
"""

from pathlib import Path
import ast


def analyze_source_files():
    """Analyze source files to identify functions and classes."""
    src_dir = Path("src/tidal_mcp")
    source_files = list(src_dir.glob("*.py"))

    analysis = {}

    for src_file in source_files:
        if src_file.name.startswith("__"):
            continue

        try:
            with open(src_file, "r") as f:
                content = f.read()
            tree = ast.parse(content)

            functions = []
            classes = []
            mcp_tools = []

            # Simple approach: look for @mcp.tool() in content

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check if this function is an MCP tool by looking at preceding lines
                    function_line = node.lineno
                    is_mcp_tool = False

                    # Check if there's an @mcp.tool decorator in the lines before this function
                    for i in range(max(0, function_line - 3), function_line):
                        if (
                            i < len(content.split("\n"))
                            and "@mcp.tool" in content.split("\n")[i]
                        ):
                            is_mcp_tool = True
                            break

                    if is_mcp_tool:
                        mcp_tools.append(node.name)
                    else:
                        functions.append(node.name)

                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)

            analysis[src_file.name] = {
                "functions": functions,
                "classes": classes,
                "mcp_tools": mcp_tools,
            }

        except Exception as e:
            print(f"Error analyzing {src_file}: {e}")

    return analysis


def analyze_test_files():
    """Analyze test files to identify test coverage."""
    test_dir = Path("tests")
    test_files = list(test_dir.glob("test_*.py"))

    test_analysis = {}

    for test_file in test_files:
        if test_file.name == "conftest.py":
            continue

        try:
            with open(test_file, "r") as f:
                content = f.read()
            tree = ast.parse(content)

            test_functions = []
            test_classes = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    test_functions.append(node.name)
                elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                    test_classes.append(node.name)

            test_analysis[test_file.name] = {
                "test_functions": test_functions,
                "test_classes": test_classes,
            }

        except Exception as e:
            print(f"Error analyzing {test_file}: {e}")

    return test_analysis


def main():
    """Generate test coverage summary."""
    print("🔍 Tidal MCP Test Coverage Summary")
    print("=" * 50)

    # Analyze source files
    source_analysis = analyze_source_files()
    test_analysis = analyze_test_files()

    print("\n📁 Source Files Analysis:")
    print("-" * 30)

    total_functions = 0
    total_classes = 0
    total_mcp_tools = 0

    for filename, data in source_analysis.items():
        print(f"\n{filename}:")
        print(f"  Classes: {len(data['classes'])}")
        print(f"  Functions: {len(data['functions'])}")
        print(f"  MCP Tools: {len(data['mcp_tools'])}")

        if data["mcp_tools"]:
            print(f"  MCP Tools: {', '.join(data['mcp_tools'])}")

        total_functions += len(data["functions"])
        total_classes += len(data["classes"])
        total_mcp_tools += len(data["mcp_tools"])

    print("\n📊 Source Totals:")
    print(f"  Total Classes: {total_classes}")
    print(f"  Total Functions: {total_functions}")
    print(f"  Total MCP Tools: {total_mcp_tools}")

    print("\n🧪 Test Files Analysis:")
    print("-" * 30)

    total_test_functions = 0
    total_test_classes = 0

    for filename, data in test_analysis.items():
        print(f"\n{filename}:")
        print(f"  Test Classes: {len(data['test_classes'])}")
        print(f"  Test Functions: {len(data['test_functions'])}")

        total_test_functions += len(data["test_functions"])
        total_test_classes += len(data["test_classes"])

    print("\n📊 Test Totals:")
    print(f"  Total Test Classes: {total_test_classes}")
    print(f"  Total Test Functions: {total_test_functions}")

    print("\n🎯 Coverage Assessment:")
    print("-" * 30)

    # Identify MCP tools coverage
    mcp_tools = []
    for data in source_analysis.values():
        mcp_tools.extend(data["mcp_tools"])

    # Check if server tests exist (covers MCP tools)
    server_test_exists = any(
        "test_server.py" in filename for filename in test_analysis.keys()
    )

    print(
        f"✅ MCP Tools ({len(mcp_tools)} total): {'Covered' if server_test_exists else 'Not Covered'}"
    )

    # Check coverage by module
    modules_covered = {
        "auth.py": any("test_auth.py" in f for f in test_analysis.keys()),
        "service.py": any("test_service.py" in f for f in test_analysis.keys()),
        "models.py": any("test_models.py" in f for f in test_analysis.keys()),
        "utils.py": any("test_utils.py" in f for f in test_analysis.keys()),
        "server.py": any("test_server.py" in f for f in test_analysis.keys()),
    }

    for module, covered in modules_covered.items():
        status = "✅ Covered" if covered else "❌ Not Covered"
        print(f"{status}: {module}")

    # Additional test categories
    additional_tests = {
        "Integration Tests": any(
            "test_integration.py" in f for f in test_analysis.keys()
        ),
        "Error Handling Tests": any(
            "test_error_handling.py" in f for f in test_analysis.keys()
        ),
        "Performance Tests": any(
            "test_performance.py" in f for f in test_analysis.keys()
        ),
    }

    print("\n🔧 Additional Test Categories:")
    for category, exists in additional_tests.items():
        status = "✅ Included" if exists else "❌ Missing"
        print(f"{status}: {category}")

    # Calculate estimated coverage
    covered_modules = sum(modules_covered.values())
    total_modules = len(modules_covered)
    coverage_percentage = (covered_modules / total_modules) * 100

    print(
        f"\n🎯 Estimated Module Coverage: {coverage_percentage:.1f}% ({covered_modules}/{total_modules} modules)"
    )

    if coverage_percentage >= 90:
        print("🎉 Excellent test coverage!")
    elif coverage_percentage >= 80:
        print("✅ Good test coverage!")
    elif coverage_percentage >= 70:
        print("⚠️  Acceptable test coverage, but could be improved")
    else:
        print("❌ Test coverage needs improvement")

    print("\n📈 Test Quality Indicators:")
    print(
        f"  Test to Code Ratio: {total_test_functions / (total_functions + total_mcp_tools + 1):.2f}"
    )
    print(f"  Tests per Source Class: {total_test_functions / (total_classes + 1):.2f}")

    return coverage_percentage >= 90


if __name__ == "__main__":
    success = main()
    print("\n" + "=" * 50)
    exit(0 if success else 1)
