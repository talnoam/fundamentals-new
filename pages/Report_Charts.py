import re
import sys
import json
import yaml
import pandas as pd
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from src.llm_analyzer import LLMAnalyzer

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / "config" / "settings.yaml"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f) or {}

charts_output_dir = config.get("visualization", {}).get("charts_output_dir", "reports/charts")
ai_reports_output_dir = config.get("visualization", {}).get("ai_reports_output_dir", "reports/ai_analysis")
CHARTS_DIR = BASE_DIR / charts_output_dir
AI_REPORTS_DIR = BASE_DIR / ai_reports_output_dir
AI_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
CHART_FILENAME_PATTERN = re.compile(
    r"^(?P<ticker>.+)_(?P<date>\d{4}-\d{2}-\d{2})_score_(?P<score>\d+)$"
)

@st.cache_data(ttl=300)
def list_report_charts():
    if not CHARTS_DIR.exists():
        return []

    charts = []
    for chart_path in CHARTS_DIR.glob("*.html"):
        match = CHART_FILENAME_PATTERN.match(chart_path.stem)
        if match:
            ticker = match.group("ticker")
            date = match.group("date")
            score = match.group("score")
        else:
            ticker = chart_path.stem
            date = "Unknown date"
            score = "N/A"

        label = f"{ticker} | {date} | score {score}"
        charts.append(
            {
                "ticker": ticker,
                "date": date,
                "score": score,
                "label": label,
                "path": chart_path,
            }
        )

    charts.sort(key=lambda item: (item["ticker"], item["date"]), reverse=True)
    return charts


@st.cache_data(ttl=300)
def load_chart_html(chart_path: Path) -> str:
    return chart_path.read_text(encoding="utf-8")


# Configure Streamlit page
st.set_page_config(
    page_title="Report Charts Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Dashboard title
st.title("📊 Report Charts Dashboard")
st.markdown("**Analyze previously generated report charts**")

charts = list_report_charts()
if charts:
    with st.expander("🏆 Latest Scan: Top Picks Summary", expanded=True):
        df_charts = pd.DataFrame(charts)
        # Convert to number for sorting
        df_charts['score'] = pd.to_numeric(df_charts['score'], errors='coerce')
        # Display the sorted table by highest score
        summary_df = df_charts[['ticker', 'date', 'score']].sort_values(by='score', ascending=False)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
else:
    st.warning("No report charts found in `reports/charts`.")
    st.stop()

# Sidebar for inputs
st.sidebar.header("Chart Parameters")

custom_ticker = st.sidebar.text_input(
    "Or enter custom ticker",
    help="Filter to a ticker that exists in reports/charts",
).upper()

available_tickers = sorted({chart["ticker"] for chart in charts})

selected_ticker = st.sidebar.selectbox(
    "Select Ticker",
    available_tickers,
    index=0,
    help="Pick a ticker from existing report charts",
)

ticker_filter = custom_ticker if custom_ticker else selected_ticker

filtered_charts = [chart for chart in charts if chart["ticker"] == ticker_filter]
if not filtered_charts:
    st.info(
        f"No report charts found for `{ticker_filter}`. "
        "Select another ticker from the sidebar."
    )
    st.stop()
chart_options = {chart["label"]: chart for chart in filtered_charts}
selected_label = st.sidebar.selectbox(
    "Select Report Chart",
    list(chart_options.keys()),
    index=0,
    help="Choose a report date and score",
)
selected_chart = chart_options[selected_label]

st.header(f"📈 {selected_chart['ticker']} Report Chart")

# Save and load analysis from disk
analysis_filename = f"{selected_chart['ticker']}_{selected_chart['date']}_analysis.json"
analysis_path = AI_REPORTS_DIR / analysis_filename
analysis_key = f"data_{selected_chart['ticker']}_{selected_chart['date']}"

# Check if analysis exists on disk and load it into Session State
if analysis_path.exists() and analysis_key not in st.session_state:
    with open(analysis_path, "r", encoding="utf-8") as f:
        st.session_state[analysis_key] = json.load(f)

col1, col2 = st.columns([3, 1])

with col1:
    st.caption(f"Date: {selected_chart['date']} | Score: {selected_chart['score']}")
    st.info("Use zoom, pan, and hover to analyze the chart interactively.")

if analysis_key in st.session_state:
    sentiment = st.session_state[analysis_key]['sentiment']
    with col2:
        if sentiment == "BULLISH":
            st.success("🟢 BULLISH")
        elif sentiment == "BEARISH":
            st.error("🔴 BEARISH")
        else:
            st.warning("🟡 NEUTRAL")

with st.spinner("Loading report chart..."):
    chart_html = load_chart_html(selected_chart["path"])
    components.html(chart_html, height=800, scrolling=True)

st.divider()
st.subheader(f"🔍 AI Equity Research: {selected_chart['ticker']}")

btn_label = f"Generate AI Analysis for {selected_chart['ticker']}" if analysis_key not in st.session_state else "Re-generate Analysis (Refresh)"

if st.button(btn_label, type="primary"):
    with st.spinner(f"Analyzing {selected_chart['ticker']} fundamentals and macro..."):
        analyzer = LLMAnalyzer()
        analysis_data = analyzer.get_equity_report(selected_chart['ticker'])

        with open(analysis_path, "w", encoding="utf-8") as f:
            json.dump(analysis_data, f, ensure_ascii=False, indent=4)

        st.session_state[analysis_key] = analysis_data
        st.toast(f"Report saved to reports/ai_analysis/{analysis_filename}", icon="💾")
        st.rerun()

# Display the analysis if it exists
if analysis_key in st.session_state:
    st.markdown(st.session_state[analysis_key]['report'])
    st.download_button(
        label="Download Analysis Report",
        data=st.session_state[analysis_key]['report'],
        file_name=f"{selected_chart['ticker']}_analysis_{selected_chart['date']}.md",
        mime="text/markdown"
    )

# Footer
st.divider()
st.markdown(
    """
<div style='text-align: center; color: gray;'>
<small>
⚠️ This is for educational purposes only and should not be considered as financial advice.
Always do your own research and consult with a financial advisor.
</small>
</div>
""",
    unsafe_allow_html=True,
)
