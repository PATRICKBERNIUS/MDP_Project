"""
Session Intensity & MDP Explorer

Interactive Streamlit app for exploring player load metrics, metabolic power demands,
and session intensity scores. Provides filtering, visualization, and summary analytics.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Optional

from mp_intensity_pipeline import build_session_intensity_df, IntensityWeights


# ============================================================================
# DATA LOADING & CACHING
# ============================================================================

@st.cache_data
def load_raw_data(path: str) -> pd.DataFrame:
    """Load raw tracking data from CSV."""
    return pd.read_csv(path)


@st.cache_data
def get_session_intensity_df(
    raw_path: str,
    w_explosiveness: float = 0.30,
    w_repeatability: float = 0.50,
    w_volume: float = 0.20
) -> pd.DataFrame:
    """
    Load raw data and compute session intensity metrics.
    Uses caching to avoid recomputation.
    """
    raw = load_raw_data(raw_path)
    weights = IntensityWeights(
        w_explosiveness=w_explosiveness,
        w_repeatability=w_repeatability,
        w_volume=w_volume
    )
    return build_session_intensity_df(raw, weights=weights)


# ============================================================================
# FILTER FUNCTIONS
# ============================================================================

def apply_filters(
    df: pd.DataFrame,
    selected_players: list,
    date_range: tuple,
    high_intensity_only: bool = False
) -> pd.DataFrame:
    """
    Apply player, date, and intensity filters to session intensity DataFrame.
    """
    filtered = df.copy()
    
    # Player filter
    if selected_players:
        filtered = filtered[filtered['player_id'].isin(selected_players)]
    
    # Date filter
    if date_range:
        start_date, end_date = date_range
        filtered = filtered[
            (filtered['date'] >= pd.Timestamp(start_date)) &
            (filtered['date'] <= pd.Timestamp(end_date))
        ]
    
    # High intensity filter
    if high_intensity_only and len(filtered) > 0:
        threshold = filtered['session_intensity_index'].quantile(0.75)
        filtered = filtered[filtered['session_intensity_index'] >= threshold]
    
    return filtered.sort_values('session_intensity_index', ascending=False)


# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def plot_intensity_over_time(df: pd.DataFrame) -> go.Figure:
    """
    Plot session intensity index over time.
    If multiple players, show separate lines per player.
    """
    if len(df) == 0:
        return go.Figure().add_annotation(text="No data to display")
    
    fig = px.line(
        df.sort_values('date'),
        x='date',
        y='session_intensity_index',
        color='player_id',
        markers=True,
        title='Session Intensity Index Over Time',
        labels={
            'date': 'Date',
            'session_intensity_index': 'Intensity Index',
            'player_id': 'Player'
        },
        hover_data=['session_id', 'mdp_10', 'total_mp_load']
    )
    fig.update_layout(height=400)
    return fig


def plot_mdp_comparison(df: pd.DataFrame) -> go.Figure:
    """
    Create a grouped bar chart comparing MDP 10/20/30 across sessions.
    """
    if len(df) == 0:
        return go.Figure().add_annotation(text="No data to display")
    
    # Prepare long-form data for MDP windows
    mdp_data = []
    for _, row in df.iterrows():
        for window in [10, 20, 30]:
            mdp_col = f'mdp_{window}'
            mdp_data.append({
                'player_id': row['player_id'],
                'session_id': row['session_id'][:15],  # Truncate for readability
                'date': row['date'],
                'window': f'{window}s',
                'mdp': row[mdp_col]
            })
    
    mdp_df = pd.DataFrame(mdp_data)
    
    fig = px.bar(
        mdp_df,
        x='session_id',
        y='mdp',
        color='window',
        title='Peak Mean Power Demand (MDP) by Window Duration',
        labels={
            'session_id': 'Session',
            'mdp': 'MDP (W)',
            'window': 'Window'
        },
        barmode='group',
        height=400
    )
    fig.update_xaxes(tickangle=45)
    return fig


def plot_intensity_distribution(df: pd.DataFrame) -> go.Figure:
    """Plot histogram of session intensity index distribution."""
    if len(df) == 0:
        return go.Figure().add_annotation(text="No data to display")
    
    fig = px.histogram(
        df,
        x='session_intensity_index',
        nbins=15,
        title='Distribution of Session Intensity Index',
        labels={'session_intensity_index': 'Intensity Index'},
        color_discrete_sequence=['#1f77b4']
    )
    fig.update_layout(height=350, showlegend=False)
    return fig


def plot_player_scatter(df: pd.DataFrame) -> go.Figure:
    """
    Scatter plot: Total MP Load vs Session Intensity Index, colored by player.
    """
    if len(df) == 0:
        return go.Figure().add_annotation(text="No data to display")
    
    fig = px.scatter(
        df,
        x='total_mp_load',
        y='session_intensity_index',
        color='player_id',
        size='mdp_10',
        hover_data=['session_id', 'date', 'mdp_10', 'mean_mp'],
        title='Session Intensity vs Total MP Load (bubble size = MDP 10s)',
        labels={
            'total_mp_load': 'Total MP Load (J)',
            'session_intensity_index': 'Intensity Index',
            'player_id': 'Player'
        },
        height=450
    )
    return fig


# ============================================================================
# SUMMARY FUNCTIONS
# ============================================================================

def compute_summary_metrics(df: pd.DataFrame) -> dict:
    """Compute summary statistics for the filtered data."""
    if len(df) == 0:
        return {
            'n_sessions': 0,
            'avg_intensity': 0.0,
            'max_intensity': 0.0,
            'avg_mdp_10': 0.0,
            'avg_total_load': 0.0
        }
    
    return {
        'n_sessions': len(df),
        'avg_intensity': df['session_intensity_index'].mean(),
        'max_intensity': df['session_intensity_index'].max(),
        'min_intensity': df['session_intensity_index'].min(),
        'avg_mdp_10': df['mdp_10'].mean(),
        'avg_total_load': df['total_mp_load'].mean()
    }


# ============================================================================
# STREAMLIT PAGE LAYOUT
# ============================================================================

def main():
    """Main Streamlit app - Coach-friendly interface."""
    
    # Page configuration
    st.set_page_config(
        page_title="Session Intensity & MDP Explorer",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🏃 Session Intensity & MDP Explorer")
    
    # Explanatory expander (coach-facing)
    with st.expander("What is the Session Intensity Index?", expanded=False):
        st.markdown("""
        **Session Intensity Index** is a standardized score that combines three key performance metrics:
        
        • **Explosiveness (30%)** – Peak power over 10 seconds (MDP 10s)  
        • **Repeatability (50%)** – Sustained power: average of 20s and 30s peaks  
        • **Volume (20%)** – Total metabolic load accumulated in the session
        
        **Scores explained**: 0 = typical session | > 1 = hard session | < -1 = light/recovery session
        """)
    
    # ========================================================================
    # SIDEBAR: FILTERS & DATA
    # ========================================================================
    
    st.sidebar.markdown("## 📊 Data & Filters")
    
    # Data source selection
    data_source = st.sidebar.radio(
        "Data Source:",
        ["Default (full_players_df.csv)", "Upload CSV"]
    )
    
    raw_path = None
    if data_source == "Upload CSV":
        uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type="csv")
        if uploaded_file:
            raw_path = uploaded_file
        else:
            st.info("👆 Please upload a CSV file to get started.")
            st.stop()
    else:
        raw_path = "full_players_df.csv"
    
    # Load session intensity data (using default weights: 0.30, 0.50, 0.20)
    try:
        session_df = get_session_intensity_df(raw_path)
    except FileNotFoundError:
        st.error(f"❌ Could not find {raw_path}. Please check the filename or upload your own data.")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        st.stop()
    
    # Player filter
    all_players = sorted(session_df['player_id'].unique().tolist())
    selected_players = st.sidebar.multiselect(
        "Select Players:",
        options=all_players,
        default=all_players
    )
    
    # Date range filter
    if len(session_df) > 0:
        min_date = session_df['date'].min().date()
        max_date = session_df['date'].max().date()
        date_range = st.sidebar.date_input(
            "Date Range:",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
    else:
        date_range = None
    
    # High intensity filter
    high_intensity_only = st.sidebar.checkbox(
        "Show only top 25% intensity",
        value=False
    )
    
    st.sidebar.markdown("---")
    st.sidebar.caption("Using default weights: Explosiveness 30% | Repeatability 50% | Volume 20%")
    
    # Apply filters
    filtered_df = apply_filters(
        session_df,
        selected_players,
        date_range,
        high_intensity_only
    )
    
    # ========================================================================
    # TOP METRICS (COACH-FRIENDLY)
    # ========================================================================
    
    metrics = compute_summary_metrics(filtered_df)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Sessions in View",
            metrics['n_sessions']
        )
    
    with col2:
        st.metric(
            "Average Session Intensity",
            f"{metrics['avg_intensity']:.2f}",
            help="0 = typical; > 1 = hard block; < -1 = light block"
        )
    
    with col3:
        st.metric(
            "Most Intense Session",
            f"{metrics['max_intensity']:.2f}",
            help="Highest intensity z-score in this view"
        )
    
    with col4:
        st.metric(
            "Average Peak 10s Power",
            f"{metrics['avg_mdp_10']:.0f} W"
        )
    
    st.markdown("---")
    
    # ========================================================================
    # MAIN SESSIONS TABLE (SLIM & READABLE)
    # ========================================================================
    
    st.subheader("📋 Sessions Summary")
    
    if len(filtered_df) > 0:
        # Create slim display table
        display_df = filtered_df[[
            'player_id', 'date', 'session_intensity_index',
            'mdp_10', 'total_mp_load', 'session_duration_s'
        ]].copy()
        
        # Rename columns for coach-friendly display
        display_df = display_df.rename(columns={
            'player_id': 'Player',
            'date': 'Date',
            'session_intensity_index': 'Intensity (z)',
            'mdp_10': 'Peak 10s Power',
            'total_mp_load': 'Total MP Load',
            'session_duration_s': 'Duration (s)'
        })
        
        # Format numeric columns
        display_df = display_df.round({
            'Intensity (z)': 2,
            'Peak 10s Power': 1,
            'Total MP Load': 0,
            'Duration (s)': 0
        })
        
        # Sort by intensity (descending)
        display_df = display_df.sort_values('Intensity (z)', ascending=False)
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # CSV Export (full dataset)
        csv_export = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download (all metrics as CSV)",
            data=csv_export,
            file_name="session_intensity_export.csv",
            mime="text/csv"
        )
        
        # Advanced metrics in expander
        with st.expander("Advanced metrics (MDP 20/30, z-scores, etc.)"):
            advanced_cols = [
                'player_id', 'session_id', 'date',
                'mdp_10', 'mdp_20', 'mdp_30',
                'explosiveness_z', 'repeatability_z', 'volume_z',
                'session_intensity_index'
            ]
            advanced_df = filtered_df[advanced_cols].copy()
            advanced_df = advanced_df.rename(columns={
                'player_id': 'Player',
                'session_id': 'Session',
                'mdp_10': 'MDP 10s',
                'mdp_20': 'MDP 20s',
                'mdp_30': 'MDP 30s',
                'explosiveness_z': 'Exp (z)',
                'repeatability_z': 'Rep (z)',
                'volume_z': 'Vol (z)',
                'session_intensity_index': 'Intensity (z)'
            })
            st.dataframe(advanced_df, use_container_width=True, hide_index=True)
    else:
        st.info("No sessions match the selected filters.")
    
    st.markdown("---")
    
    # ========================================================================
    # HERO CHART: INTENSITY OVER TIME
    # ========================================================================
    
    st.subheader("📈 Session Intensity Over Time")
    
    if len(filtered_df) > 0:
        fig = plot_intensity_over_time(filtered_df)
        # Add reference lines
        fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Typical")
        fig.add_hline(y=1, line_dash="dot", line_color="red", annotation_text="Hard")
        fig.add_hline(y=-1, line_dash="dot", line_color="blue", annotation_text="Light")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data to display.")
    
    # ========================================================================
    # SUPPORTING CHART: INTENSITY VS LOAD
    # ========================================================================
    
    st.subheader("💪 Session Intensity vs Total MP Load")
    
    if len(filtered_df) > 0:
        st.plotly_chart(plot_player_scatter(filtered_df), use_container_width=True)
    else:
        st.info("No data to display.")
    
    st.markdown("---")
    
    # ========================================================================
    # EXTRA DETAIL IN EXPANDER
    # ========================================================================
    
    with st.expander("More detail: intensity distribution and MDP windows"):
        col1, col2 = st.columns(2)
        
        with col1:
            if len(filtered_df) > 0:
                st.plotly_chart(plot_intensity_distribution(filtered_df), use_container_width=True)
            else:
                st.info("No data to display.")
        
        with col2:
            if len(filtered_df) > 0:
                st.plotly_chart(plot_mdp_comparison(filtered_df), use_container_width=True)
            else:
                st.info("No data to display.")
    
    st.markdown("---")
    
    # ========================================================================
    # PEAK HIGHLIGHTS (RENAMED & SLIMMED)
    # ========================================================================
    
    st.subheader("⚡ Peak Performance Highlights (Top 5)")
    
    if len(filtered_df) > 0:
        col1, col2, col3 = st.columns(3)
        
        # Top Explosive Sessions
        with col1:
            st.markdown("**Most Explosive**")
            top_explosive = filtered_df.nlargest(5, 'mdp_10')[[
                'player_id', 'date', 'session_id', 'mdp_10', 'session_intensity_index'
            ]].copy()
            top_explosive = top_explosive.rename(columns={
                'player_id': 'Player',
                'date': 'Date',
                'session_id': 'Session',
                'mdp_10': 'Peak 10s',
                'session_intensity_index': 'Intensity'
            })
            top_explosive = top_explosive.round({'Peak 10s': 0, 'Intensity': 2})
            st.dataframe(top_explosive, use_container_width=True, hide_index=True)
        
        # Best Sustained Effort
        with col2:
            st.markdown("**Best Sustained Effort**")
            filtered_df_copy = filtered_df.copy()
            filtered_df_copy['sustained'] = 0.5 * (filtered_df_copy['mdp_20'] + filtered_df_copy['mdp_30'])
            top_sustained = filtered_df_copy.nlargest(5, 'sustained')[[
                'player_id', 'date', 'session_id', 'mdp_20', 'session_intensity_index'
            ]].copy()
            top_sustained = top_sustained.rename(columns={
                'player_id': 'Player',
                'date': 'Date',
                'session_id': 'Session',
                'mdp_20': 'Peak 20s',
                'session_intensity_index': 'Intensity'
            })
            top_sustained = top_sustained.round({'Peak 20s': 0, 'Intensity': 2})
            st.dataframe(top_sustained, use_container_width=True, hide_index=True)
        
        # Biggest Workload
        with col3:
            st.markdown("**Biggest Workload**")
            top_load = filtered_df.nlargest(5, 'total_mp_load')[[
                'player_id', 'date', 'session_id', 'total_mp_load', 'session_intensity_index'
            ]].copy()
            top_load = top_load.rename(columns={
                'player_id': 'Player',
                'date': 'Date',
                'session_id': 'Session',
                'total_mp_load': 'Total Load',
                'session_intensity_index': 'Intensity'
            })
            top_load = top_load.round({'Total Load': 0, 'Intensity': 2})
            st.dataframe(top_load, use_container_width=True, hide_index=True)
    else:
        st.info("No sessions to highlight.")
    
    st.markdown("---")
    
    # Footer
    st.caption(
        "Session Intensity & MDP Explorer | Default: E=30%, R=50%, V=20% | Grow Irish Performance Analytics"
    )


if __name__ == '__main__':
    main()
