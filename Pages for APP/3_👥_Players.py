"""
Player Analysis Page - Grow Irish Performance Analytics
Coach/Analyst Dual-Mode Design

Displays player-centric intensity metrics with role-based UX:
- Coach Mode: Quick narrative snapshots (5-10 second read)
- Analyst Mode: Full metrics, charts, exports, team comparisons

Helper functions for modular, testable rendering.
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Optional, List, Dict
from datetime import date
from utils import (
    load_and_clean,
    calculate_intensity_and_windows,
    compute_session_mdp_info,
    compute_early_late_comparison,
    plot_rolling_window_lines,
    add_mdp_overlays_to_plot
)
from coach_metrics_engine import (
    get_player_session_metrics,
    generate_coach_insights,
    ordinal_suffix
)
from intensity_utils import (
    compute_mdp,
    format_mdp_display,
    format_percentile,
    format_z_score,
    classify_intensity
)


# ============================================================================
# HELPER: BUILD TEAM AVERAGE DATAFRAME
# ============================================================================

def build_team_average_dataframe(session_data: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate session_data across all players to create a 'team average' dataframe.
    Returns mean intensity values per timestamp for Coach view.
    """
    if session_data is None or len(session_data) == 0:
        return pd.DataFrame()
    
    agg_dict = {}
    intensity_cols = [col for col in session_data.columns if 'intensity' in col]
    for col in intensity_cols:
        agg_dict[col] = 'mean'
    
    # Also aggregate other metrics
    numeric_cols = session_data.select_dtypes(include=['number']).columns
    for col in numeric_cols:
        if col not in agg_dict:
            agg_dict[col] = 'mean'
    
    if 'timestamp' in session_data.columns:
        team_avg = session_data.groupby('timestamp').agg(agg_dict).reset_index()
    else:
        team_avg = session_data[list(agg_dict.keys())].mean().to_frame().T
    
    return team_avg


# ============================================================================
# CENTRALIZED MDP METRICS HELPER
# ============================================================================

def compute_player_mdp_metrics(player_session_df: pd.DataFrame) -> dict:
    """
    Single source of truth for all peak metrics in a player session.
    
    Consolidates logic from snapshot and MDP summary. Returns consistent dict
    used across all sections (snapshot, MDP summary, insights, exports).
    
    Args:
        player_session_df: DataFrame for single player + session, sorted by timestamp
    
    Returns:
        Dict with keys:
        - mdp_5, mdp_10, mdp_20, mdp_30: Peak values (W) or None
        - mdp_peak_value: Highest peak across all windows
        - mdp_peak_window: Window size of peak (e.g., '20s')
        - data_quality: Dict with coverage %, sample count
        - has_peak_data: Boolean, true if any peak found
    """
    if player_session_df is None or len(player_session_df) == 0:
        return {
            'mdp_5': None, 'mdp_10': None, 'mdp_20': None, 'mdp_30': None,
            'mdp_peak_value': None, 'mdp_peak_window': None,
            'data_quality': {'coverage': 0, 'samples': 0},
            'has_peak_data': False
        }
    
    metrics = {}
    
    # Compute each window's max if column exists
    for window_size in [5, 10, 20, 30]:
        col_name = f'intensity_{window_size}s'
        if col_name in player_session_df.columns:
            max_val = player_session_df[col_name].max()
            metrics[f'mdp_{window_size}'] = float(max_val) if pd.notna(max_val) else None
        else:
            metrics[f'mdp_{window_size}'] = None
    
    # Find overall peak
    peak_values = [v for v in [metrics['mdp_5'], metrics['mdp_10'], metrics['mdp_20'], metrics['mdp_30']] if v is not None]
    if peak_values:
        metrics['mdp_peak_value'] = max(peak_values)
        for window_size in [5, 10, 20, 30]:
            if metrics[f'mdp_{window_size}'] == metrics['mdp_peak_value']:
                metrics['mdp_peak_window'] = f'{window_size}s'
                break
    else:
        metrics['mdp_peak_value'] = None
        metrics['mdp_peak_window'] = None
    
    # Data quality assessment
    samples_available = len(player_session_df)
    if 'timestamp' in player_session_df.columns and samples_available > 1:
        session_start = player_session_df['timestamp'].min()
        session_end = player_session_df['timestamp'].max()
        total_seconds = (session_end - session_start).total_seconds()
        pct_coverage = (samples_available / max(1, total_seconds)) * 100 if total_seconds > 0 else 100
        pct_coverage = min(100, pct_coverage)
    else:
        pct_coverage = 100 if samples_available > 0 else 0
    
    metrics['data_quality'] = {'coverage': pct_coverage, 'samples': samples_available}
    metrics['has_peak_data'] = any(v is not None for v in [metrics['mdp_5'], metrics['mdp_10'], metrics['mdp_20'], metrics['mdp_30']])
    
    return metrics


# ============================================================================
# HELPER FUNCTIONS: COACH BACKBONE SECTIONS
# ============================================================================

def render_session_snapshot(
    metrics_row: Optional[pd.Series],
    selected_player_display: str,
    view_mode: str
) -> None:
    """
    Render session snapshot using coach metrics.
    
    Args:
        metrics_row: Row from coach metrics DataFrame, or None
        selected_player_display: Player name/number for display
        view_mode: "Coach" or "Analyst"
    """
    st.markdown("---")
    st.markdown("## 📊 Session Snapshot")
    st.caption(f"Performance metrics for {selected_player_display}.")
    
    if metrics_row is None or metrics_row.empty or pd.isna(metrics_row.get('intensity_score')):
        st.info("No metrics available for selected player-session.")
        return
    
    # Extract metrics
    intensity_percentile = metrics_row.get('intensity_percentile')
    intensity_category = metrics_row.get('intensity_category')
    z_intensity = metrics_row.get('z_intensity')
    mdp10 = metrics_row.get('mdp10')
    mdp20 = metrics_row.get('mdp20')
    mdp30 = metrics_row.get('mdp30')
    total_load = metrics_row.get('total_load')
    baseline = metrics_row.get('baseline_28d_intensity')
    
    # Render 5 metric tiles
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if pd.notna(intensity_percentile):
            st.metric(
                "Intensity",
                format_percentile(intensity_percentile),
                delta=intensity_category if intensity_category and intensity_category != "Unknown" else None
            )
        else:
            st.metric("Intensity", "N/A")
    
    with col2:
        if pd.notna(mdp10):
            st.metric("Peak 10s (W/kg)", f"{mdp10:.1f}")
        else:
            st.metric("Peak 10s (W/kg)", "N/A")
    
    with col3:
        if pd.notna(mdp20):
            st.metric("Peak 20s (W/kg)", f"{mdp20:.1f}")
        else:
            st.metric("Peak 20s (W/kg)", "N/A")
    
    col4, col5 = st.columns(2)
    
    with col4:
        if pd.notna(mdp30):
            st.metric("Peak 30s (W/kg)", f"{mdp30:.1f}")
        else:
            st.metric("Peak 30s (W/kg)", "N/A")
    
    with col5:
        if pd.notna(total_load):
            st.metric("Total Load (AU)", f"{total_load:.0f}")
        else:
            st.metric("Total Load (AU)", "N/A")
    
    # Optional z-score and baseline display
    if pd.notna(z_intensity):
        st.caption(f"📈 Z-score: {format_z_score(z_intensity)}")
    if pd.notna(baseline):
        st.caption(f"📊 28-day baseline intensity percentile: **{baseline:.0f}th**")


def render_team_comparison(
    metrics_row: Optional[pd.Series],
    view_mode: str
) -> dict:
    """
    Render team percentile comparison.
    
    Args:
        metrics_row: Row from coach metrics DataFrame, or None
        view_mode: "Coach" or "Analyst"
    
    Returns:
        Dict with percentile values for use in insights
    """
    st.markdown("---")
    st.markdown("## 🏆 Team Comparison")
    st.caption("This player's percentile rank relative to teammates in this session.")
    
    percentiles = {
        'intensity_pct': None,
        'peak10_pct': None,
        'total_load_pct': None
    }
    
    if metrics_row is None or metrics_row.empty:
        st.info("No team data available.")
        return percentiles
    
    intensity_pct = metrics_row.get('intensity_percentile')
    peak10_pct = metrics_row.get('peak10_percentile')
    total_load_pct = metrics_row.get('total_load_percentile')
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if pd.notna(intensity_pct):
            st.metric("Intensity Percentile", ordinal_suffix(int(intensity_pct)))
            percentiles['intensity_pct'] = intensity_pct
        else:
            st.metric("Intensity Percentile", "N/A")
    
    with col2:
        if pd.notna(peak10_pct):
            st.metric("Peak 10s Percentile", ordinal_suffix(int(peak10_pct)))
            percentiles['peak10_pct'] = peak10_pct
        else:
            st.metric("Peak 10s Percentile", "N/A")
    
    with col3:
        if pd.notna(total_load_pct):
            st.metric("Total Load Percentile", ordinal_suffix(int(total_load_pct)))
            percentiles['total_load_pct'] = total_load_pct
        else:
            st.metric("Total Load Percentile", "N/A")
    
    return percentiles


def render_early_mid_late_trend(
    metrics_row: Optional[pd.Series],
    view_mode: str
) -> dict:
    """
    Render early/mid/late intensity trend using coach metrics.
    
    Args:
        metrics_row: Row from coach metrics DataFrame, or None
        view_mode: "Coach" or "Analyst"
    
    Returns:
        Dict with trend info for use in insights
    """
    if metrics_row is None or metrics_row.empty:
        return {}
    
    early_mp = metrics_row.get('early_mp')
    mid_mp = metrics_row.get('mid_mp')
    late_mp = metrics_row.get('late_mp')
    
    # Check if we have enough data
    if all(pd.isna(x) for x in [early_mp, mid_mp, late_mp]):
        return {}
    
    st.markdown("---")
    st.markdown("## 📈 Intensity Trend: Early / Mid / Late")
    st.caption("How intensity changed throughout the session.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if pd.notna(early_mp):
            st.metric("Early (1st third)", f"{early_mp:.1f} W/kg")
        else:
            st.metric("Early (1st third)", "N/A")
    
    with col2:
        if pd.notna(mid_mp):
            st.metric("Mid (2nd third)", f"{mid_mp:.1f} W/kg")
        else:
            st.metric("Mid (2nd third)", "N/A")
    
    with col3:
        if pd.notna(late_mp):
            st.metric("Late (3rd third)", f"{late_mp:.1f} W/kg")
        else:
            st.metric("Late (3rd third)", "N/A")
    
    # Compute trend
    trend_data = {}
    if pd.notna(early_mp) and pd.notna(late_mp) and early_mp > 0:
        trend_change = late_mp - early_mp
        trend_pct = (trend_change / early_mp) * 100
        trend_data['trend_change'] = trend_change
        trend_data['trend_pct'] = trend_pct
        
        # Emoji and interpretation
        if trend_pct > 5:
            emoji = "📈"
            interpretation = f"Increasing (↑ {trend_pct:+.1f}%)"
        elif trend_pct < -5:
            emoji = "📉"
            interpretation = f"Decreasing (↓ {trend_pct:+.1f}%)"
        else:
            emoji = "➡️"
            interpretation = f"Stable (±{abs(trend_pct):.1f}%)"
        
        st.caption(f"{emoji} **{interpretation}** from early to late")
    
    return trend_data


def render_coach_insights(
    metrics_row: Optional[pd.Series],
    selected_player_display: str,
    view_mode: str
) -> None:
    """
    Render natural-language coach insights from metrics.
    
    Args:
        metrics_row: Row from coach metrics DataFrame, or None
        selected_player_display: Player name/number for display
        view_mode: "Coach" or "Analyst"
    """
    st.markdown("---")
    st.markdown("## 💡 Coach's Insights")
    
    if metrics_row is None or metrics_row.empty:
        st.info("Insufficient data for insights.")
        return
    
    # Generate insights using the coach metrics engine
    insights = generate_coach_insights(metrics_row)
    
    if insights:
        for i, insight in enumerate(insights, 1):
            st.info(f"• {insight}")
    else:
        st.caption("No actionable insights available for this session.")


# ============================================================================
# HELPER FUNCTIONS: ANALYST-ONLY SECTIONS
# ============================================================================

def render_intensity_chart(session_data: pd.DataFrame, selected_player_id: Optional[str],
                          selected_player_display: str, window_options: List[str], mdp_info: Optional[List],
                          selected_session_idx: int, session_options: List[str], view_mode: str) -> None:
    """Render intensity over time: time series with rolling windows. Analyst-only."""
    st.markdown("---")
    st.markdown("## 📈 Intensity Over Time (Detailed)")
    
    if selected_player_id is None:
        plot_data = session_data.groupby('timestamp')[window_options].mean().reset_index()
        title_suffix = "All Players (Average)"
    else:
        plot_data = session_data[session_data['player_id'] == selected_player_id].copy()
        title_suffix = selected_player_display
    
    if len(plot_data) > 0:
        if len(window_options) > 3:
            st.info("💡 You've selected many windows. Consider unchecking some for clarity.")
        
        fig = plot_rolling_window_lines(plot_data, window_options)
        
        if mdp_info and selected_player_id is not None:
            fig = add_mdp_overlays_to_plot(fig, mdp_info, show_overlays=True, active_windows=['10s', '20s'])
        
        fig.update_layout(title=f"{session_options[selected_session_idx]} – {title_suffix}",
                         xaxis_title="Time", yaxis_title="Intensity")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Use this plot to see when intensity peaked and how effort changed.")
    else:
        st.warning("No data available for selected filters.")


def render_mdp_summary(player_session_df: Optional[pd.DataFrame], metrics_row: Optional[pd.Series], view_mode: str) -> None:
    """
    Render detailed MDP summary: 4-window breakdown using canonical compute_mdp.
    Analyst-only.
    
    Args:
        player_session_df: Player's session data (single player only, sorted by timestamp)
        metrics_row: Row from coach metrics with pre-computed mdp10, mdp20, mdp30
        view_mode: "Coach" or "Analyst"
    """
    if player_session_df is None or len(player_session_df) == 0:
        return
    
    st.markdown("---")
    st.markdown("## 🔥 MDP Summary (Analyst Detail)")
    st.caption("Peaks show highest rolling average metabolic power for each window.")
    
    # Get MP series for computing MDPs
    if 'mp' in player_session_df.columns:
        mp_series = player_session_df['mp'].dropna()
        if mp_series.empty:
            st.info("No MP data available for MDP computation.")
            return
        
        # Use canonical compute_mdp function
        mdp5, _ = compute_mdp(mp_series, 5)
        mdp10, _ = compute_mdp(mp_series, 10)
        mdp20, _ = compute_mdp(mp_series, 20)
        mdp30, _ = compute_mdp(mp_series, 30)
    else:
        # Fallback: use metrics_row values if available
        if metrics_row is not None:
            mdp5 = metrics_row.get('mdp10')  # Approximate with 10s
            mdp10 = metrics_row.get('mdp10')
            mdp20 = metrics_row.get('mdp20')
            mdp30 = metrics_row.get('mdp30')
        else:
            st.info("No MP data available for MDP computation.")
            return
    
    # Render 4 metric tiles
    mdp_col1, mdp_col2, mdp_col3, mdp_col4 = st.columns(4)
    windows_order = [5, 10, 20, 30]
    mdp_values = [mdp5, mdp10, mdp20, mdp30]
    cols = [mdp_col1, mdp_col2, mdp_col3, mdp_col4]
    
    for window_size, mdp_val, col in zip(windows_order, mdp_values, cols):
        with col:
            if pd.notna(mdp_val):
                st.metric(f"Peak {window_size}s", format_mdp_display(mdp_val))
            else:
                st.metric(f"Peak {window_size}s", "N/A")
    
    # Data quality indicator
    data_coverage = len(player_session_df) / max(1, len(player_session_df))
    coverage_color = "🟢" if data_coverage >= 0.8 else "🟡" if data_coverage >= 0.5 else "🔴"
    st.caption(f"{coverage_color} Data: {len(player_session_df)} samples")


def render_analyst_exports(session_data: pd.DataFrame, selected_player_id: Optional[str],
                           selected_date, view_mode: str) -> None:
    """
    Render export tools for Analyst. Minimal layout.
    
    Args:
        session_data: Full session data
        selected_player_id: Selected player (or None for "All Players")
        selected_date: Session date
        view_mode: "Coach" or "Analyst"
    """
    st.markdown("---")
    st.markdown("## 📥 Export for Further Analysis")
    
    # Export full session data or player-specific data
    if selected_player_id is None:
        export_data = session_data.copy()
        export_name = "all_players"
    else:
        export_data = session_data[session_data['player_id'] == selected_player_id].copy()
        export_name = f"player_{selected_player_id}"
    
    if not export_data.empty:
        csv_data = export_data.to_csv(index=False)
        st.download_button(
            label="📥 Download session data (CSV)",
            data=csv_data,
            file_name=f"{export_name}_{selected_date.date() if hasattr(selected_date, 'date') else selected_date}.csv",
            mime="text/csv"
        )
        st.caption(f"Dataset: {len(export_data)} rows × {len(export_data.columns)} columns")
    else:
        st.info("No data available for export.")


def render_team_peaks_table(session_data: pd.DataFrame, view_mode: str) -> None:
    """
    [DEPRECATED] Render team peaks table: all players' max intensities.
    
    This section is removed from the Analyst layout. Analysts can export data
    and analyze team performance in downstream tools.
    """
    pass  # No longer rendered


# ============================================================================
# PAGE INITIALIZATION
# ============================================================================

st.set_page_config(page_title="Player Analysis", layout="wide")
st.title("⚡ Player Analysis")
st.caption("Compare individual and team performance across rolling intensity windows.")

# ============================================================================
# DATA LOADING
# ============================================================================

if 'data_loaded' not in st.session_state:
    st.session_state['data_loaded'] = False
    st.session_state['raw_df'] = None
    st.session_state['hr_df'] = None

if 'weights' not in st.session_state:
    st.session_state['weights'] = {'power_W': 0.5, 'heart_rate_bpm': 0.3, 'cadence_rpm': 0.2}

if not st.session_state.get('data_loaded', False) or st.session_state['raw_df'] is None:
    st.warning("⚠️ Please load data on the **Home** page first.")
    st.stop()

raw_df = st.session_state['raw_df']
hr_df = st.session_state['hr_df']
intensity_weights = st.session_state['weights']

# Compute session intensity
with st.spinner("Computing session intensity and rolling windows..."):
    # Ensure required columns exist
    required_cols = ['speed', 'acc', 'hr', 'mp']
    available_cols = [col for col in required_cols if col in raw_df.columns]
    
    if len(available_cols) >= 3:  # Need at least 3 of the 4
        session_data, _ = calculate_intensity_and_windows(
            raw_df,
            w_speed=0.25,
            w_acc=0.25,
            w_hr=0.25,
            w_mp=0.25,
            columns_to_plot=available_cols
        )
    else:
        # Fallback: use raw data directly
        st.warning("⚠️ Not all intensity columns available. Using raw data directly.")
        session_data = raw_df.copy()

session_data['date'] = pd.to_datetime(session_data['date'])
session_dates = sorted(session_data['date'].unique())

# ============================================================================
# SESSION & PLAYER SELECTION
# ============================================================================

col1, col2, col3 = st.columns(3)

# Session selector
with col1:
    session_options = [d.strftime("%Y-%m-%d") for d in session_dates]
    default_session_idx = len(session_options) - 1 if session_options else 0
    
    if 'selected_session_idx' not in st.session_state:
        st.session_state['selected_session_idx'] = default_session_idx
    
    selected_session_idx = st.selectbox("Session:", range(len(session_options)),
                                       format_func=lambda i: session_options[i],
                                       index=st.session_state['selected_session_idx'],
                                       key='player_session_select')
    st.session_state['selected_session_idx'] = selected_session_idx
    selected_date = session_dates[selected_session_idx]
    
    # Filter session data
    session_data = session_data[session_data['date'] == selected_date].copy()

# Player selector
with col2:
    if 'player_number' in session_data.columns:
        player_map = session_data[['player_number', 'player_id']].drop_duplicates().sort_values('player_number')
        player_options = ["All Players (Average)"] + [f"Player {int(num)}" for num in player_map['player_number']]
        player_id_map = dict(zip([f"Player {int(num)}" for num in player_map['player_number']], player_map['player_id']))
        player_id_map["All Players (Average)"] = None
    else:
        player_options = ["All Players (Average)"] + sorted(session_data['player_id'].unique())
        player_id_map = {p: p if p != "All Players (Average)" else None for p in player_options}
    
    if 'viz_player' not in st.session_state:
        st.session_state['viz_player'] = player_options[0]
    
    try:
        current_player_idx = player_options.index(st.session_state.get('viz_player', player_options[0]))
    except (ValueError, KeyError):
        current_player_idx = 0
        st.session_state['viz_player'] = player_options[0]
    
    selected_player_display = st.selectbox("Player:", player_options, index=current_player_idx, key='player_select')
    st.session_state['viz_player'] = selected_player_display
    selected_player_id = player_id_map.get(selected_player_display, None)

# Window selector
with col3:
    window_choices = ['intensity', 'intensity_5s', 'intensity_10s', 'intensity_20s', 'intensity_30s']
    
    if 'viz_windows' not in st.session_state:
        st.session_state['viz_windows'] = ['intensity', 'intensity_10s', 'intensity_20s']
    
    window_options = st.multiselect("Intensity Windows:", window_choices,
                                   default=st.session_state['viz_windows'],
                                   key='player_window_select',
                                   help="Choose which intensity windows to plot on the chart.")
    st.session_state['viz_windows'] = window_options

# Note: window_options can be empty in Coach mode; Analyst charts will show warning if not selected.

# ============================================================================
# VIEW MODE TOGGLE (GLOBAL)
# ============================================================================

if 'player_view_mode' not in st.session_state:
    st.session_state['player_view_mode'] = 'Coach'

player_view_mode = st.radio("View Mode:", ["Coach", "Analyst"],
                            index=0 if st.session_state['player_view_mode'] == 'Coach' else 1,
                            horizontal=True, key='player_view_mode_radio',
                            help="Coach: Quick insights. Analyst: Full metrics, charts, exports.")
st.session_state['player_view_mode'] = player_view_mode

# ============================================================================
# DATA PREPARATION & COACH METRICS COMPUTATION
# ============================================================================

# Compute coach metrics for the current session
metrics_df = None
metrics_row = None
mdp_info = None

try:
    # Use coach metrics engine to compute all player metrics
    metrics_df = get_player_session_metrics(
        session_data=session_data,
        session_date=selected_date.date() if hasattr(selected_date, 'date') else selected_date,
        all_player_metrics_by_date=None  # Can be extended for 28-day baseline later
    )
    
    # Get the row for the selected player
    if metrics_df is not None and not metrics_df.empty:
        if selected_player_id is not None:
            metrics_row = metrics_df[metrics_df['player_id'] == selected_player_id]
            if not metrics_row.empty:
                metrics_row = metrics_row.iloc[0]
            else:
                metrics_row = None
        else:
            # "All Players" mode: compute aggregate
            if len(metrics_df) > 0:
                # Average across all players
                numeric_cols = metrics_df.select_dtypes(include=['number']).columns
                metrics_row = metrics_df[numeric_cols].mean()
                metrics_row['player_name'] = 'Team Average'

except Exception as e:
    st.warning(f"Error computing coach metrics: {str(e)}")
    metrics_df = None
    metrics_row = None

# For analyst mode, still compute old-style MDP info if needed
mdp_info = None
if metrics_row is not None and selected_player_id is not None:
    try:
        df_player_session = session_data[session_data['player_id'] == selected_player_id].copy()
        if not df_player_session.empty and 'timestamp' in df_player_session.columns:
            df_player_session = df_player_session.sort_values('timestamp').reset_index(drop=True)
            mdp_info = compute_session_mdp_info(df_player_session)
    except:
        pass

# ============================================================================
# RENDER SECTIONS
# ============================================================================

# COACH BACKBONE: Always render these sections if metrics exist
if metrics_row is not None and not pd.isna(metrics_row.get('intensity_score', np.nan)):
    # Backbone sections (always visible in both Coach and Analyst modes)
    render_session_snapshot(metrics_row, selected_player_display, player_view_mode)
    
    percentiles = render_team_comparison(metrics_row, player_view_mode)
    
    trend_data = render_early_mid_late_trend(metrics_row, player_view_mode)
    
    render_coach_insights(metrics_row, selected_player_display, player_view_mode)
    
    # ANALYST-ONLY SECTIONS: Only render if Analyst mode is selected
    if player_view_mode == "Analyst":
        # Get player session data for analyst visualizations
        if selected_player_id is not None:
            df_player_session = session_data[session_data['player_id'] == selected_player_id].copy()
            if not df_player_session.empty and 'timestamp' in df_player_session.columns:
                df_player_session = df_player_session.sort_values('timestamp').reset_index(drop=True)
        else:
            df_player_session = build_team_average_dataframe(session_data)
        
        # Analyst layout: clean, minimal flow
        # 1. Intensity over time chart
        render_intensity_chart(session_data, selected_player_id, selected_player_display,
                              window_options, mdp_info, selected_session_idx, session_options, player_view_mode)
        
        # 2. MDP Summary with real metrics
        render_mdp_summary(df_player_session if not df_player_session.empty else None, metrics_row, player_view_mode)
        
        # 3. Export section (minimal)
        render_analyst_exports(session_data, selected_player_id, selected_date, player_view_mode)
else:
    st.info("No session data available for the selected filters. Please check your data or selection.")

st.markdown("---")
st.caption("Player Analysis | Grow Irish Performance Analytics")
