import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import sys
from datetime import datetime

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from src.version_manager import VersionManager

# Page configuration
st.set_page_config(
    page_title="Backtest Analytics",
    page_icon="📈",
    layout="wide"
)

# Display version in sidebar
VersionManager.display_version_sidebar()

# Title
st.title("📈 Scanner Performance Backtest Analytics")
st.markdown("""
Evaluate the historical performance of scanner suggestions using real market data.
This analysis validates the quality of our pattern detection and scoring algorithms.
""")

# Load data
@st.cache_data(ttl=3600)
def load_backtest_data(csv_path: str = "reports/backtest_summary.csv") -> pd.DataFrame:
    """Load backtest results from CSV."""
    path = Path(csv_path)
    if not path.exists():
        return pd.DataFrame()
    
    df = pd.read_csv(path)
    # Convert date columns to datetime
    date_cols = ['analysis_date', 'entry_date', 'max_return_date', 'max_drawdown_date', 'current_date']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
    
    return df

# Load data
df = load_backtest_data()

if df.empty:
    st.warning("⚠️ No backtest data available. Run `python stock_scanner/analyze_results.py` to generate backtest results.")
    st.info("The backtest analyzer will scan `reports/charts/` directory and evaluate historical performance of all scanner suggestions.")
    st.stop()

# Sidebar filters
st.sidebar.header("🔍 Filters")

# Score filter
min_score = int(df['score'].min())
max_score = int(df['score'].max())
score_range = st.sidebar.slider(
    "Scanner Score Range",
    min_value=min_score,
    max_value=max_score,
    value=(min_score, max_score)
)

# Outcome filter
outcome_options = df['outcome'].unique().tolist()
selected_outcomes = st.sidebar.multiselect(
    "Outcome",
    options=outcome_options,
    default=outcome_options
)

# Index filter
index_options = df['index'].unique().tolist()
selected_indices = st.sidebar.multiselect(
    "Index Membership",
    options=index_options,
    default=index_options
)

# Date range filter
min_date = df['analysis_date'].min().date()
max_date = df['analysis_date'].max().date()
date_range = st.sidebar.date_input(
    "Analysis Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Apply filters
filtered_df = df[
    (df['score'] >= score_range[0]) &
    (df['score'] <= score_range[1]) &
    (df['outcome'].isin(selected_outcomes)) &
    (df['index'].isin(selected_indices))
]

# Apply date filter
if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[
        (filtered_df['analysis_date'].dt.date >= start_date) &
        (filtered_df['analysis_date'].dt.date <= end_date)
    ]

# Calculate key metrics
total_signals = len(filtered_df)
completed_trades = filtered_df[filtered_df['outcome'].isin(['Success', 'Failure'])]
success_count = (filtered_df['outcome'] == 'Success').sum()
failure_count = (filtered_df['outcome'] == 'Failure').sum()
pending_count = (filtered_df['outcome'] == 'Pending').sum()

hit_rate = (success_count / len(completed_trades) * 100) if len(completed_trades) > 0 else 0
avg_max_return = filtered_df['max_return_pct'].mean()
avg_current_return = filtered_df['current_return_pct'].mean()

# Display key metrics
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Signals", total_signals)

with col2:
    st.metric("Hit Rate", f"{hit_rate:.1f}%")

with col3:
    st.metric("Success", success_count, delta=f"{success_count - failure_count:+d}")

with col4:
    st.metric("Avg Max Return", f"{avg_max_return:.2f}%")

with col5:
    st.metric("Avg Current Return", f"{avg_current_return:.2f}%")

# Tabs for different analyses
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview", 
    "🎯 Score Analysis", 
    "📅 Time Series", 
    "🏆 Performance Leaders",
    "📋 Raw Data"
])

with tab1:
    st.header("Performance Overview")
    
    # Outcome distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Outcome Distribution")
        outcome_counts = filtered_df['outcome'].value_counts()
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=outcome_counts.index,
            values=outcome_counts.values,
            hole=0.3,
            marker=dict(colors=['#00cc96', '#ef553b', '#636efa'])
        )])
        fig_pie.update_layout(
            template='plotly_dark',
            height=400
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader("Performance by Index")
        
        index_stats = filtered_df.groupby('index').agg({
            'outcome': lambda x: (x == 'Success').sum() / ((x == 'Success').sum() + (x == 'Failure').sum()) * 100 if ((x == 'Success').sum() + (x == 'Failure').sum()) > 0 else 0,
            'max_return_pct': 'mean',
            'ticker': 'count'
        }).reset_index()
        index_stats.columns = ['Index', 'Hit Rate %', 'Avg Max Return %', 'Count']
        
        fig_index = go.Figure()
        fig_index.add_trace(go.Bar(
            x=index_stats['Index'],
            y=index_stats['Hit Rate %'],
            name='Hit Rate %',
            marker_color='#00cc96'
        ))
        fig_index.add_trace(go.Bar(
            x=index_stats['Index'],
            y=index_stats['Avg Max Return %'],
            name='Avg Max Return %',
            marker_color='#636efa'
        ))
        fig_index.update_layout(
            template='plotly_dark',
            barmode='group',
            height=400,
            yaxis_title='Percentage'
        )
        st.plotly_chart(fig_index, use_container_width=True)
    
    # Return distribution
    st.subheader("Return Distribution")
    
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Histogram(
        x=filtered_df['max_return_pct'],
        nbinsx=30,
        name='Max Return %',
        marker_color='#636efa',
        opacity=0.7
    ))
    fig_hist.add_trace(go.Histogram(
        x=filtered_df['current_return_pct'],
        nbinsx=30,
        name='Current Return %',
        marker_color='#00cc96',
        opacity=0.7
    ))
    fig_hist.update_layout(
        template='plotly_dark',
        height=400,
        barmode='overlay',
        xaxis_title='Return %',
        yaxis_title='Count'
    )
    st.plotly_chart(fig_hist, use_container_width=True)

with tab2:
    st.header("Score Analysis")
    
    # Score vs Return scatter
    st.subheader("Scanner Score vs Maximum Return")
    
    fig_scatter = go.Figure()
    
    # Color by outcome
    for outcome in filtered_df['outcome'].unique():
        df_outcome = filtered_df[filtered_df['outcome'] == outcome]
        color = '#00cc96' if outcome == 'Success' else '#ef553b' if outcome == 'Failure' else '#636efa'
        
        fig_scatter.add_trace(go.Scatter(
            x=df_outcome['score'],
            y=df_outcome['max_return_pct'],
            mode='markers',
            name=outcome,
            marker=dict(
                size=8,
                color=color,
                line=dict(width=1, color='white')
            ),
            text=df_outcome['ticker'],
            hovertemplate='<b>%{text}</b><br>Score: %{x}<br>Max Return: %{y:.2f}%<extra></extra>'
        ))
    
    # Add trendline for completed trades
    if len(completed_trades) > 1:
        z = np.polyfit(completed_trades['score'], completed_trades['max_return_pct'], 1)
        p = np.poly1d(z)
        x_trend = np.linspace(completed_trades['score'].min(), completed_trades['score'].max(), 100)
        
        fig_scatter.add_trace(go.Scatter(
            x=x_trend,
            y=p(x_trend),
            mode='lines',
            name='Trend',
            line=dict(color='yellow', dash='dash', width=2)
        ))
    
    fig_scatter.update_layout(
        template='plotly_dark',
        height=500,
        xaxis_title='Scanner Score',
        yaxis_title='Max Return %',
        hovermode='closest'
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Score distribution by outcome
    st.subheader("Score Distribution by Outcome")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_box = go.Figure()
        for outcome in filtered_df['outcome'].unique():
            df_outcome = filtered_df[filtered_df['outcome'] == outcome]
            fig_box.add_trace(go.Box(
                y=df_outcome['score'],
                name=outcome,
                boxmean='sd'
            ))
        
        fig_box.update_layout(
            template='plotly_dark',
            height=400,
            yaxis_title='Scanner Score'
        )
        st.plotly_chart(fig_box, use_container_width=True)
    
    with col2:
        # Correlation analysis
        if len(completed_trades) > 1:
            score_corr = completed_trades['score'].corr(completed_trades['max_return_pct'])
            avg_score_success = completed_trades[completed_trades['outcome'] == 'Success']['score'].mean()
            avg_score_failure = completed_trades[completed_trades['outcome'] == 'Failure']['score'].mean()
            
            st.metric("Score-Return Correlation", f"{score_corr:.3f}")
            st.metric("Avg Score (Success)", f"{avg_score_success:.1f}")
            st.metric("Avg Score (Failure)", f"{avg_score_failure:.1f}")
            
            if score_corr > 0.3:
                st.success("✅ Strong positive correlation - higher scores predict better returns")
            elif score_corr > 0:
                st.info("ℹ️ Weak positive correlation - scores have some predictive power")
            else:
                st.warning("⚠️ Negative or no correlation - scores need improvement")

with tab3:
    st.header("Time Series Analysis")
    
    # Hit rate over time
    st.subheader("Hit Rate Over Time (30-Day Rolling Window)")
    
    # Sort by date and calculate rolling hit rate
    time_df = completed_trades.sort_values('analysis_date').copy()
    time_df['success_numeric'] = (time_df['outcome'] == 'Success').astype(int)
    time_df['rolling_hit_rate'] = time_df['success_numeric'].rolling(window=30, min_periods=5).mean() * 100
    
    fig_time = go.Figure()
    fig_time.add_trace(go.Scatter(
        x=time_df['analysis_date'],
        y=time_df['rolling_hit_rate'],
        mode='lines',
        name='30-Day Rolling Hit Rate',
        line=dict(color='#00cc96', width=2),
        fill='tozeroy'
    ))
    
    fig_time.update_layout(
        template='plotly_dark',
        height=400,
        xaxis_title='Analysis Date',
        yaxis_title='Hit Rate %',
        hovermode='x unified'
    )
    st.plotly_chart(fig_time, use_container_width=True)
    
    # Cumulative returns simulation
    st.subheader("Cumulative Returns Simulation")
    st.markdown("*Assuming equal-weighted portfolio of all signals*")
    
    cumulative_df = filtered_df.sort_values('analysis_date').copy()
    cumulative_df['cumulative_avg_return'] = cumulative_df['current_return_pct'].expanding().mean()
    
    fig_cumul = go.Figure()
    fig_cumul.add_trace(go.Scatter(
        x=cumulative_df['analysis_date'],
        y=cumulative_df['cumulative_avg_return'],
        mode='lines',
        name='Cumulative Avg Return',
        line=dict(color='#636efa', width=2),
        fill='tozeroy'
    ))
    
    fig_cumul.update_layout(
        template='plotly_dark',
        height=400,
        xaxis_title='Analysis Date',
        yaxis_title='Cumulative Average Return %',
        hovermode='x unified'
    )
    st.plotly_chart(fig_cumul, use_container_width=True)

with tab4:
    st.header("Performance Leaders & Laggards")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Top 10 Best Performers")
        top_performers = filtered_df.nlargest(10, 'max_return_pct')[
            ['ticker', 'analysis_date', 'score', 'max_return_pct', 'outcome', 'index']
        ].copy()
        top_performers['analysis_date'] = top_performers['analysis_date'].dt.strftime('%Y-%m-%d')
        
        # Style the dataframe
        st.dataframe(
            top_performers.style.format({
                'score': '{:.0f}',
                'max_return_pct': '{:.2f}%'
            }),
            use_container_width=True,
            hide_index=True
        )
    
    with col2:
        st.subheader("📉 Top 10 Worst Performers")
        worst_performers = filtered_df.nsmallest(10, 'max_return_pct')[
            ['ticker', 'analysis_date', 'score', 'max_return_pct', 'outcome', 'index']
        ].copy()
        worst_performers['analysis_date'] = worst_performers['analysis_date'].dt.strftime('%Y-%m-%d')
        
        # Style the dataframe
        st.dataframe(
            worst_performers.style.format({
                'score': '{:.0f}',
                'max_return_pct': '{:.2f}%'
            }),
            use_container_width=True,
            hide_index=True
        )
    
    # High score failures analysis
    st.subheader("⚠️ High Score Failures (Score >= 85)")
    high_score_failures = filtered_df[
        (filtered_df['score'] >= 85) & 
        (filtered_df['outcome'] == 'Failure')
    ][['ticker', 'analysis_date', 'score', 'max_return_pct', 'max_drawdown_pct', 'holding_days']].copy()
    
    if not high_score_failures.empty:
        high_score_failures['analysis_date'] = high_score_failures['analysis_date'].dt.strftime('%Y-%m-%d')
        st.dataframe(
            high_score_failures.style.format({
                'score': '{:.0f}',
                'max_return_pct': '{:.2f}%',
                'max_drawdown_pct': '{:.2f}%',
                'holding_days': '{:.0f}'
            }),
            use_container_width=True,
            hide_index=True
        )
        st.warning(f"Found {len(high_score_failures)} high-score failures. These cases should be investigated for pattern improvements.")
    else:
        st.success("✅ No high-score failures found!")

with tab5:
    st.header("Raw Backtest Data")
    
    # Display options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        sort_by = st.selectbox(
            "Sort by",
            options=['analysis_date', 'score', 'max_return_pct', 'current_return_pct', 'ticker'],
            index=0
        )
    
    with col2:
        sort_order = st.radio("Order", options=['Descending', 'Ascending'], horizontal=True)
    
    with col3:
        max_rows = max(10, len(filtered_df))  # Ensure max is at least 10
        default_rows = min(50, len(filtered_df)) if len(filtered_df) > 0 else 10
        show_rows = st.number_input("Rows to display", min_value=10, max_value=max_rows, value=default_rows)
    
    # Sort and display
    display_df = filtered_df.sort_values(
        by=sort_by,
        ascending=(sort_order == 'Ascending')
    ).head(show_rows).copy()
    
    # Format dates
    date_cols = ['analysis_date', 'entry_date', 'max_return_date', 'max_drawdown_date', 'current_date']
    for col in date_cols:
        if col in display_df.columns:
            display_df[col] = display_df[col].dt.strftime('%Y-%m-%d')
    
    st.dataframe(
        display_df.style.format({
            'entry_price': '${:.2f}',
            'score': '{:.0f}',
            'max_return_pct': '{:.2f}%',
            'max_drawdown_pct': '{:.2f}%',
            'current_return_pct': '{:.2f}%',
            'holding_days': '{:.0f}'
        }),
        use_container_width=True,
        hide_index=True
    )
    
    # Download button
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Filtered Data as CSV",
        data=csv,
        file_name=f"backtest_filtered_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

# Footer
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Data source: reports/backtest_summary.csv")
