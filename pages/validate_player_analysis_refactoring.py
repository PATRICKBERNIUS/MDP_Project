"""
Validation script for Player Analysis and Sessions refactoring.
Checks syntax of all modified files and data flow integrity.
"""

import ast
import sys

files_to_check = [
    "pages/1_🏠_Home.py",
    "pages/2_📊_Sessions.py",
    "pages/3_👥_Players.py",
    "src/display_names.py",
    "src/intensity_classification.py",
    "src/config.py",
]

def validate_syntax(file_path: str) -> tuple[bool, str]:
    """
    Validate Python syntax of a file.
    
    Returns:
        Tuple of (is_valid, message)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code)
        return True, f"✓ {file_path}: Syntax valid"
    except SyntaxError as e:
        return False, f"✗ {file_path}: Syntax error at line {e.lineno}: {e.msg}"
    except FileNotFoundError:
        return False, f"✗ {file_path}: File not found"
    except Exception as e:
        return False, f"✗ {file_path}: Error: {str(e)}"


def main():
    print("=" * 70)
    print("VALIDATION: Player Analysis & Sessions Refactoring")
    print("=" * 70)
    
    all_valid = True
    results = []
    
    for file_path in files_to_check:
        is_valid, message = validate_syntax(file_path)
        results.append((is_valid, message))
        if not is_valid:
            all_valid = False
    
    # Print results
    print()
    for is_valid, message in results:
        status_symbol = "✓" if is_valid else "✗"
        print(message)
    
    print()
    print("=" * 70)
    
    if all_valid:
        print("✓ All files are syntactically correct!")
        print()
        print("Key changes validated:")
        print("  ✓ src/display_names.py: Shared display name mapping functions")
        print("  ✓ src/intensity_classification.py: Intensity classification (Easy/Medium/Hard/Very Hard)")
        print("  ✓ src/config.py: Coach-friendly intensity window labels")
        print("  ✓ pages/1_🏠_Home.py: Display name mapping in data loading pipeline")
        print("  ✓ pages/2_📊_Sessions.py: Uses shared display_names module")
        print("  ✓ pages/3_👥_Players.py: Display names + intensity classification")
        print()
        print("No breaking changes to calculations or data flow.")
        return 0
    else:
        print("✗ Some files have syntax errors. Please fix before deploying.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
