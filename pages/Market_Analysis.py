import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the chart functions from report.py
from report import create_candlestick_chart, create_multi_indicator_chart

# Configure Streamlit page
st.set_page_config(
    page_title="Market Analysis Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Market indicators mapping (display name: ticker symbol)
MARKET_INDICATORS = {
    "Bitcoin (BTC-USD)": "BTC-USD",
    "S&P 500 (GSPC)": "^GSPC",
    "NASDAQ Composite (IXIC)": "^IXIC",
    "NASDAQ 100 (NDX)": "^NDX",
    "Russell 2000 (RUT)": "^RUT",
    "Dow Jones (DJI)": "^DJI",
    "10-Year Treasury (TNX)": "^TNX",
    "Crude Oil": "CL=F",
    "Gold": "GC=F",
    "Silver": "SI=F",
    "VIX (Volatility Index)": "^VIX",
    "US Dollar Index": "DX-Y.NYB"
}

# Initialize session state
if 'current_market_indicator' not in st.session_state:
    st.session_state.current_market_indicator = None
if 'current_years' not in st.session_state:
    st.session_state.current_years = 1

# Dashboard title
st.title("🌍 Market Analysis Dashboard")
st.markdown("**Analyze key market indicators and economic data**")

# Sidebar for inputs
st.sidebar.header("Chart Parameters")

# Market indicator selection - allow multiple selections
indicator_names = list(MARKET_INDICATORS.keys())
selected_indicator_names = st.sidebar.multiselect(
    "Select Market Indicators",
    indicator_names,
    default=[indicator_names[0]] if indicator_names else [],
    help="Choose one or more market indicators to analyze. Select multiple to compare on the same chart."
)

# Get the ticker symbols for selected indicators
selected_tickers = {name: MARKET_INDICATORS[name] for name in selected_indicator_names}

# Period selector
period_option = st.sidebar.radio(
    "Select Time Period",
    ["Custom Years", "1 Day", "7 Days", "1 Month", "6 Months", "Year to Date"],
    index=3,  # Default to 1 Month
    help="Choose a predefined period or custom years"
)

# Years selector (only show if Custom Years is selected)
if period_option == "Custom Years":
    years = st.sidebar.slider(
        "Years of Historical Data",
        min_value=1,
        max_value=10,
        value=1,
        help="Select how many years of historical data to display"
    )
else:
    years = None  # Will be calculated based on period_option

# Chart options (only show for single indicator)
if len(selected_indicator_names) == 1:
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
    
    # Support and Resistance levels
    st.sidebar.markdown("---")
    show_support_resistance = st.sidebar.checkbox(
        "Show Support & Resistance Levels",
        value=False,
        help="Automatically calculate and display support (green) and resistance (red) levels"
    )
else:
    sma_periods = []
    show_support_resistance = False

# Normalization option for multiple indicators
if len(selected_indicator_names) > 1:
    st.sidebar.markdown("---")
    normalize_chart = st.sidebar.checkbox(
        "Normalize to Percentage Change",
        value=True,
        help="Normalize all indicators to percentage change from start date for better comparison"
    )
else:
    normalize_chart = False

# Update session state
st.session_state.current_years = years

# Main content area
if selected_indicator_names:
    if len(selected_indicator_names) == 1:
        # Single indicator - use candlestick chart with full features
        indicator_name = selected_indicator_names[0]
        ticker = selected_tickers[indicator_name]
        
        st.header(f"📊 {indicator_name} Price Chart")
        
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
            if period_option == "Custom Years":
                period_text = f"{years} years"
            else:
                period_text = period_option.lower()
            st.info(f"Showing {timeframe.lower()} data for {period_text}")
        
        # Create and display the chart
        with st.spinner("Loading chart..."):
            # Pass SMA periods if any are selected
            sma_list = sma_periods if sma_periods else None
            fig = create_candlestick_chart(
                ticker, 
                years, 
                timeframe, 
                sma_periods=sma_list,
                show_support_resistance=show_support_resistance,
                period_option=period_option if period_option != "Custom Years" else None
            )
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Unable to load chart data")
    else:
        # Multiple indicators - use comparison chart
        st.header(f"📊 Market Indicators Comparison")
        
        # Chart controls
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            timeframe = st.selectbox(
                "Select Timeframe",
                ["Daily", "Weekly", "Monthly"],
                index=0,  # Default to Daily
                help="Choose the timeframe for the chart"
            )
        
        with col2:
            st.info(f"Comparing {len(selected_indicator_names)} indicators")
        
        with col3:
            if period_option == "Custom Years":
                period_text = f"{years} years"
            else:
                period_text = period_option.lower()
            st.info(f"Showing {timeframe.lower()} data for {period_text}")
        
        # Show selected indicators
        indicators_text = ', '.join(selected_indicator_names)
        st.markdown(f"**Selected Indicators:** {indicators_text}")
        
        # Create and display the chart
        with st.spinner("Loading chart..."):
            fig = create_multi_indicator_chart(
                selected_tickers,
                years,
                timeframe,
                normalize=normalize_chart,
                period_option=period_option if period_option != "Custom Years" else None
            )
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Unable to load chart data")
else:
    st.info("👈 Please select one or more market indicators from the sidebar to view the chart")

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

