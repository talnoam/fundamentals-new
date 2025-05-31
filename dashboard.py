import streamlit as st
import pandas as pd
from datetime import datetime

# Import the analysis functions from report.py
from report import analyze_company, display_analysis_results

# Configure Streamlit page
st.set_page_config(
    page_title="Fundamentals Investment Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dashboard title
st.title("📊 Fundamentals Investment Dashboard")
st.markdown("**Long-term investment analysis for profitable companies (3-5 years)**")

# Sidebar for inputs
st.sidebar.header("Investment Parameters")

# Ticker input
ticker = st.sidebar.text_input("Enter Stock Ticker", value="NVDA", help="Enter the stock symbol (e.g., AAPL, NVDA, TSLA)")

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
        
        # Display the results
        display_analysis_results(results)

elif not ticker and analyze_button:
    st.warning("Please enter a ticker symbol to analyze.")

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