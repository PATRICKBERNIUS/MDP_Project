import re

files = {
    'pages/1_🏠_Home.py': 'home',
    'pages/2_📊_Sessions.py': 'sessions',
    'pages/3_👥_Players.py': 'players',
    'pages/4_⚡_Configuration.py': 'config',
    'pages/5_📚_Documentation.py': 'docs'
}

print("=" * 70)
print("NAVIGATION VERIFICATION")
print("=" * 70)

all_good = True

for filepath, expected_page in files.items():
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for import
    has_import = 'from src.ui.nav import render_global_nav' in content
    
    # Check for render call
    render_pattern = rf'render_global_nav\(current_page=["\']' + expected_page
    has_render = bool(re.search(render_pattern, content))
    
    # Check order: page_config, render_global_nav, st.title
    page_config_pos = content.find('st.set_page_config')
    render_pos = content.find(f'render_global_nav(current_page="{expected_page}")')
    title_pos = content.find('st.title(')
    
    correct_order = page_config_pos < render_pos < title_pos if all(x != -1 for x in [page_config_pos, render_pos, title_pos]) else False
    
    status = "✅" if (has_import and has_render and correct_order) else "❌"
    
    if not (has_import and has_render and correct_order):
        all_good = False
    
    print(f"\n{status} {filepath}")
    print(f"   Import: {'✅' if has_import else '❌'}")
    print(f"   Render call: {'✅' if has_render else '❌'}")
    print(f"   Correct order (config → nav → title): {'✅' if correct_order else '❌'}")

print("\n" + "=" * 70)
if all_good:
    print("✅ ALL PAGES CORRECTLY CONFIGURED")
else:
    print("❌ SOME PAGES NEED FIXES")
print("=" * 70)
