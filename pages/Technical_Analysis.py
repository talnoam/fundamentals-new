import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the chart function from report.py
from report import create_candlestick_chart
from report_utils import get_all_tickers

# Configure Streamlit page
st.set_page_config(
    page_title="Technical Analysis Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'current_ticker' not in st.session_state:
    st.session_state.current_ticker = None
if 'current_years' not in st.session_state:
    st.session_state.current_years = 3

# Dashboard title
st.title("📈 Technical Analysis Dashboard")
st.markdown("**Price chart analysis and technical indicators**")

# Sidebar for inputs
st.sidebar.header("Chart Parameters")

# Create a search box for custom ticker input
custom_ticker = st.sidebar.text_input(
    "Or enter custom ticker",
    help="Enter any valid stock symbol"
).upper()

# Get all tickers
tickers = get_all_tickers()

# Create a selectbox with search functionality
selected_ticker = st.sidebar.selectbox(
    "Select Stock",
    tickers,
    index=tickers.index("NVDA") if "NVDA" in tickers else 0,
    help="Search for any available stock symbol"
)

# Use custom ticker if provided, otherwise use selected ticker
ticker = custom_ticker if custom_ticker else selected_ticker

# Years selector
years = st.sidebar.slider(
    "Years of Historical Data",
    min_value=1,
    max_value=10,
    value=1,
    help="Select how many years of historical data to display"
)

# SMA indicators selection
st.sidebar.header("Technical Indicators")
st.sidebar.markdown("**Simple Moving Averages (SMA)**")

sma_20 = st.sidebar.checkbox("SMA 20", value=False, help="20-period Simple Moving Average")
sma_50 = st.sidebar.checkbox("SMA 50", value=False, help="50-period Simple Moving Average")
sma_150 = st.sidebar.checkbox("SMA 150", value=False, help="150-period Simple Moving Average")
sma_200 = st.sidebar.checkbox("SMA 200", value=False, help="200-period Simple Moving Average")

# Collect selected SMA periods
sma_periods = []
if sma_20:
    sma_periods.append(20)
if sma_50:
    sma_periods.append(50)
if sma_150:
    sma_periods.append(150)
if sma_200:
    sma_periods.append(200)

# Update session state
st.session_state.current_ticker = ticker
st.session_state.current_years = years

# Main content area
if ticker:
    st.header(f"📊 {ticker.upper()} Price Chart")
    
    # Chart controls
    col1, col2 = st.columns([1, 3])
    
    with col1:
        timeframe = st.selectbox(
            "Select Timeframe",
            ["Daily", "Weekly", "Monthly"],
            index=0,  # Default to Daily
            help="Choose the timeframe for the candlestick chart"
        )
    
    with col2:
        st.info(f"Showing {timeframe.lower()} data for the last {years} years")
    
    # Create and display the chart
    with st.spinner("Loading chart..."):
        # Pass SMA periods if any are selected
        sma_list = sma_periods if sma_periods else None
        fig = create_candlestick_chart(ticker, years, timeframe, sma_periods=sma_list)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Unable to load chart data")
else:
    st.info("👈 Please select a ticker from the sidebar to view the chart")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray;'>
<small>
⚠️ This is for educational purposes only and should not be considered as financial advice. 
Always do your own research and consult with a financial advisor.
</small>
</div>
""", unsafe_allow_html=True)

