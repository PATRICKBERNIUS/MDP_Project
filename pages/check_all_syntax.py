#!/usr/bin/env python
import ast
import sys

files_to_check = [
    'utils.py',
    'pages/2_📊_Sessions.py'
]

all_valid = True
for filepath in files_to_check:
    try:
        with open(filepath, encoding='utf-8') as f:
            ast.parse(f.read())
        print(f"✓ {filepath}: Syntax valid")
    except SyntaxError as e:
        print(f"✗ {filepath}: Syntax error: {e}")
        all_valid = False
    except Exception as e:
        print(f"✗ {filepath}: Error: {e}")
        all_valid = False

if all_valid:
    print("\n✓ All files are syntactically correct")
    sys.exit(0)
else:
    sys.exit(1)
