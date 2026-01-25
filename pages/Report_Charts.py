import re
import sys
import json
import yaml
import pandas as pd
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from src.llm_analyzer import LLMAnalyzer
from src.version_manager import VersionManager
from stock_scanner.scanner import StockScanner
from src.ticker_provider import TickerProvider 

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

def display_analysis_section(ticker, date, report_type):
    """helper function to display the analysis results by type"""
    filename = f"{ticker}_{date}_{report_type}.json"
    path = AI_REPORTS_DIR / filename
    
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # display the sentiment
        sentiment = data.get('sentiment', 'NEUTRAL')
        if sentiment == "BULLISH": st.success(f"🟢 SENTIMENT: {sentiment}")
        elif sentiment == "BEARISH": st.error(f"🔴 SENTIMENT: {sentiment}")
        else: st.warning(f"🟡 SENTIMENT: {sentiment}")
        
        st.markdown(data.get('report', ''))
        st.download_button(
            label=f"Download {report_type.capitalize()} Report",
            data=data.get('report', ''),
            file_name=f"{ticker}_{report_type}_{date}.md",
            mime="text/markdown",
            key=f"dl_{ticker}_{report_type}"
        )
    else:
        st.info(f"No {report_type} analysis generated yet.")


# Configure Streamlit page
st.set_page_config(
    page_title="Report Charts Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# display the version in the sidebar
VersionManager.display_version_sidebar()

# Sidebar - Scanner trigger button
st.sidebar.header("🔍 Stock Scanner")
if st.sidebar.button("🚀 Run Stock Scanner", type="primary", use_container_width=True):
    with st.sidebar:
        with st.spinner("Running stock scanner..."):
            try:
                # Initialize scanner and ticker provider
                scanner = StockScanner()
                provider = TickerProvider(cache_expiry_days=1)
                
                # Fetch all tickers
                tickers_to_scan = provider.get_all_tickers(
                    include_nasdaq=True, 
                    include_sp500=True, 
                    include_dow=True
                )
                
                # Run the scan
                scanner.scan(tickers_to_scan)
                
                st.sidebar.success("✅ Scan completed! Check the reports/charts directory for new charts.")
                st.cache_data.clear()  # Clear cache to refresh the chart list
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"❌ Error running scanner: {str(e)}")
                st.sidebar.exception(e)

# Dashboard title
st.title("📊 Report Charts Dashboard")
st.markdown("**Analyze previously generated report charts**")

charts = list_report_charts()
if not charts:
    st.warning("No report charts found in `reports/charts`.")
    st.stop()

# Sidebar for inputs
st.sidebar.header("Chart Parameters")

# Date selection
available_dates = sorted({chart["date"] for chart in charts}, reverse=True)
selected_date = st.sidebar.selectbox(
    "Select Date",
    ["All dates"] + available_dates,
    index=0,
    help="Filter charts by report date",
)

# Filter charts by date
if selected_date == "All dates":
    date_filtered_charts = charts
else:
    date_filtered_charts = [chart for chart in charts if chart["date"] == selected_date]

if not date_filtered_charts:
    st.info(f"No report charts found for date `{selected_date}`.")
    st.stop()

# Sort by score (highest first) within the date selection
date_filtered_charts.sort(
    key=lambda item: (
        pd.to_numeric(item["score"], errors='coerce') if item["score"] != "N/A" else -1
    ),
    reverse=True
)

# Top Picks Summary - filtered by selected date
with st.expander("🏆 Latest Scan: Top Picks Summary", expanded=True):
    df_charts = pd.DataFrame(date_filtered_charts)
    # Convert to number for sorting
    df_charts['score'] = pd.to_numeric(df_charts['score'], errors='coerce')
    # Display the sorted table by highest score
    summary_df = df_charts[['ticker', 'date', 'score']].sort_values(by='score', ascending=False)
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

custom_ticker = st.sidebar.text_input(
    "Or enter custom ticker",
    help="Filter to a ticker that exists in reports/charts",
).upper()

available_tickers = sorted({chart["ticker"] for chart in date_filtered_charts})

selected_ticker = st.sidebar.selectbox(
    "Select Ticker",
    available_tickers,
    index=0,
    help="Pick a ticker from existing report charts",
)

ticker_filter = custom_ticker if custom_ticker else selected_ticker

filtered_charts = [chart for chart in date_filtered_charts if chart["ticker"] == ticker_filter]
if not filtered_charts:
    st.info(
        f"No report charts found for `{ticker_filter}`. "
        "Select another ticker from the sidebar."
    )
    st.stop()

# Charts are already sorted by score (highest first) from date_filtered_charts
chart_options = {chart["label"]: chart for chart in filtered_charts}
selected_label = st.sidebar.selectbox(
    "Select Report Chart",
    list(chart_options.keys()),
    index=0,
    help="Choose a report chart (sorted by highest score first)",
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


st.caption(f"Date: {selected_chart['date']} | Score: {selected_chart['score']}")
st.info("Use zoom, pan, and hover to analyze the chart interactively.")


with st.spinner("Loading report chart..."):
    chart_html = load_chart_html(selected_chart["path"])
    components.html(chart_html, height=800, scrolling=True)

st.divider()
st.subheader(f"🔍 AI Analysis Tools: {selected_chart['ticker']}")

# buttons for the different analyses
col1, col2 = st.columns(2)
analyzer = LLMAnalyzer(config.get("llm_analysis", {}))

with col1:
    if st.button("🚀 Generate Fundamental Analysis", use_container_width=True):
        with st.spinner("Running deep fundamental research..."):
            res = analyzer.get_equity_report(selected_chart['ticker'], report_type="fundamental")
            with open(AI_REPORTS_DIR / f"{selected_chart['ticker']}_{selected_chart['date']}_fundamental.json", "w") as f:
                json.dump(res, f)
            st.rerun()

with col2:
    if st.button("🔥 Validate Breakout Momentum", type="primary", use_container_width=True):
        with st.spinner("Analyzing catalyst and short-term flow..."):
            res = analyzer.get_equity_report(selected_chart['ticker'], report_type="breakout")
            with open(AI_REPORTS_DIR / f"{selected_chart['ticker']}_{selected_chart['date']}_breakout.json", "w") as f:
                json.dump(res, f)
            st.rerun()

# display the analysis results in tabs
tab_fund, tab_break = st.tabs(["📋 Fundamental Research", "⚡ Breakout Validation"])

with tab_fund:
    display_analysis_section(selected_chart['ticker'], selected_chart['date'], "fundamental")

with tab_break:
    display_analysis_section(selected_chart['ticker'], selected_chart['date'], "breakout")

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
