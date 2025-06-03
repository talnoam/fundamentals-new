import streamlit as st
import pandas as pd

# Import the analysis functions from report.py
from report import analyze_company, display_analysis_results, create_candlestick_chart
from report_utils import get_all_tickers

# Configure Streamlit page
st.set_page_config(
    page_title="Fundamentals Investment Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'current_ticker' not in st.session_state:
    st.session_state.current_ticker = None
if 'current_years' not in st.session_state:
    st.session_state.current_years = None

# Dashboard title
st.title("📊 Fundamentals Investment Dashboard")
st.markdown("**Long-term investment analysis for profitable companies (3-5 years)**")

# Sidebar for inputs
st.sidebar.header("Investment Parameters")

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

# Investment parameters
years_to_estimate = st.sidebar.slider("Years to Estimate", min_value=3, max_value=5, value=3)
margin_of_safety = st.sidebar.slider("Margin of Safety (%)", min_value=5, max_value=30, value=10) / 100
ir_required = st.sidebar.checkbox("Include Investor Relations Link", value=False)

# Analysis button
analyze_button = st.sidebar.button("🔍 Analyze Company", type="primary")

# Main application logic
if analyze_button and ticker:
    with st.spinner(f"Analyzing {ticker.upper()}..."):
        # Run the analysis using the clean function from report.py
        results = analyze_company(
            ticker=ticker,
            years_to_estimate=years_to_estimate,
            margin_of_safety=margin_of_safety,
            ir_required=ir_required
        )
        
        # Store results in session state
        st.session_state.analysis_results = results
        st.session_state.current_ticker = ticker
        st.session_state.current_years = years_to_estimate

elif not ticker and analyze_button:
    st.warning("Please enter a ticker symbol to analyze.")

# Display analysis results if they exist in session state
if st.session_state.analysis_results is not None:
    # Display the results
    display_analysis_results(st.session_state.analysis_results)
    
    # Add candlestick chart section
    st.divider()
    st.header("📈 Price Chart Analysis")
    
    # Chart controls
    col1, col2 = st.columns([1, 3])
    
    with col1:
        timeframe = st.selectbox(
            "Select Timeframe",
            ["Daily", "Weekly", "Monthly"],
            index=1,  # Default to Weekly
            help="Choose the timeframe for the candlestick chart"
        )
    
    with col2:
        st.info(f"Showing {timeframe.lower()} data for the last {st.session_state.current_years} years")
    
    # Create and display the chart
    with st.spinner("Loading chart..."):
        fig = create_candlestick_chart(st.session_state.current_ticker, st.session_state.current_years, timeframe)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Unable to load chart data")

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