import ast
import sys

files = [
    'pages/1_🏠_Home.py',
    'pages/2_📊_Sessions.py', 
    'pages/3_👥_Players.py',
    'pages/4_⚡_Configuration.py',
    'pages/5_📚_Documentation.py',
    'src/ui/nav.py'
]

errors = []
for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            ast.parse(file.read())
        print(f"✅ {f}")
    except SyntaxError as e:
        errors.append(f"❌ {f}: {e}")
        print(f"❌ {f}: {e}")

if errors:
    sys.exit(1)
else:
    print("\n✅ All files have valid Python syntax")
