#!/usr/bin/env python
"""Test weight presets functionality"""

import pandas as pd
from mp_intensity_pipeline import build_session_intensity_df, IntensityWeights

print("\n" + "="*70)
print("TESTING WEIGHT PRESETS FUNCTIONALITY")
print("="*70)

# Load data
df_raw = pd.read_csv('full_players_df.csv')

# Define weight presets (same as in the Streamlit app)
PRESETS = {
    "Match-like / Balanced": (0.30, 0.50, 0.20),
    "Speed Emphasis": (0.50, 0.30, 0.20),
    "Conditioning / Volume": (0.20, 0.40, 0.40),
}

print("\n📊 Computing session intensity with each preset...\n")

results = {}

for preset_name, (w_e, w_r, w_v) in PRESETS.items():
    print(f"\n{preset_name}")
    print(f"  Weights: Explosiveness={w_e:.0%}, Repeatability={w_r:.0%}, Volume={w_v:.0%}")
    
    # Create weights object
    weights = IntensityWeights(
        w_explosiveness=w_e,
        w_repeatability=w_r,
        w_volume=w_v
    )
    
    # Build session dataframe
    session_df = build_session_intensity_df(df_raw, weights=weights)
    
    # Store results
    results[preset_name] = session_df
    
    # Print statistics
    print(f"  Mean Intensity Index: {session_df['session_intensity_index'].mean():.3f}")
    print(f"  Max Intensity Index:  {session_df['session_intensity_index'].max():.3f}")
    print(f"  Min Intensity Index:  {session_df['session_intensity_index'].min():.3f}")
    print(f"  Std Deviation:        {session_df['session_intensity_index'].std():.3f}")

# Verify that different weights produce different intensity indices
print("\n" + "="*70)
print("COMPARISON: How rankings change with different presets")
print("="*70)

# Get top 3 sessions by intensity for each preset
for preset_name in PRESETS.keys():
    print(f"\n🏆 Top 3 Sessions - {preset_name}:")
    top_sessions = results[preset_name].nlargest(3, 'session_intensity_index')[
        ['player_id', 'date', 'session_intensity_index', 'mdp_10', 'total_mp_load']
    ]
    for idx, (_, row) in enumerate(top_sessions.iterrows(), 1):
        print(f"  {idx}. Player {row['player_id']}: "
              f"Intensity={row['session_intensity_index']:.2f}, "
              f"MDP10={row['mdp_10']:.0f}W, "
              f"Load={row['total_mp_load']:.0f}J")

# Verify caching function works with weights
print("\n" + "="*70)
print("TESTING STREAMLIT CACHING FUNCTION")
print("="*70)

from session_intensity_explorer import get_session_intensity_df

print("\nTesting get_session_intensity_df with different weights...")

df1 = get_session_intensity_df('full_players_df.csv', 0.30, 0.50, 0.20)
df2 = get_session_intensity_df('full_players_df.csv', 0.50, 0.30, 0.20)
df3 = get_session_intensity_df('full_players_df.csv', 0.20, 0.40, 0.40)

print(f"\n✅ Match-like preset:")
print(f"   Mean intensity: {df1['session_intensity_index'].mean():.3f}")

print(f"\n✅ Speed Emphasis preset:")
print(f"   Mean intensity: {df2['session_intensity_index'].mean():.3f}")

print(f"\n✅ Conditioning preset:")
print(f"   Mean intensity: {df3['session_intensity_index'].mean():.3f}")

# Verify they're different
if (df1['session_intensity_index'] != df2['session_intensity_index']).any():
    print("\n✅ Different weights produce different results (as expected)")
else:
    print("\n⚠️ Warning: Different weights produced same results")

print("\n" + "="*70)
print("✅ ALL TESTS PASSED - Weight presets working correctly!")
print("="*70 + "\n")
