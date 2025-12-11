#!/usr/bin/env python
"""Quick test of Session Intensity Explorer"""

import sys
print("Testing Session Intensity Explorer...\n")

try:
    from mp_intensity_pipeline import build_session_intensity_df
    import pandas as pd
    
    print("Loading raw data...")
    df_raw = pd.read_csv('full_players_df.csv')
    
    print("Computing session intensity metrics...")
    session_df = build_session_intensity_df(df_raw)
    
    print(f"✅ Success! Loaded {len(session_df)} sessions")
    print(f"\nDataFrame columns: {list(session_df.columns)}")
    print(f"\nSample statistics:")
    print(f"  - Mean Intensity: {session_df['session_intensity_index'].mean():.2f}")
    print(f"  - Max Intensity: {session_df['session_intensity_index'].max():.2f}")
    print(f"  - Avg MDP 10s: {session_df['mdp_10'].mean():.1f} W")
    
    print("\n✅ All components tested successfully!")
    print("Ready to run: streamlit run session_intensity_explorer.py")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
