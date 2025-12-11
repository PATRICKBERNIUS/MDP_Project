import ast
import sys

files = [
    'intensity_utils.py',
    'coach_metrics_engine.py',
    'pages/3_👥_Players.py'
]

for fpath in files:
    try:
        with open(fpath, encoding='utf-8') as f:
            ast.parse(f.read())
        print(f"✓ {fpath}: Syntax valid")
    except SyntaxError as e:
        print(f"✗ {fpath}: {e}")
        sys.exit(1)

print("\n✓ All files syntax validated")
