#!/usr/bin/env python
import ast
import sys

try:
    with open('pages/2_📊_Sessions.py', encoding='utf-8') as f:
        code = f.read()
    ast.parse(code)
    print("✓ Sessions file syntax is valid")
    sys.exit(0)
except SyntaxError as e:
    print(f"✗ Syntax error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
