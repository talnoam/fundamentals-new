import streamlit as st

# Configure Streamlit page
st.set_page_config(
    page_title="Investment Analysis Dashboards",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Landing page content
st.title("📊 Investment Analysis Dashboards")
st.markdown("""
Welcome to the Investment Analysis platform! Choose a dashboard from the sidebar to get started.

## Available Dashboards

### 📊 Fundamentals Dashboard
Comprehensive fundamental analysis for long-term investment decisions (3-5 years):
- Historical financial data and trends
- Growth rate calculations
- Future price projections
- Intrinsic value estimation
- Risk assessment
- Investment recommendations

### 📈 Technical Analysis Dashboard
Price chart analysis and technical indicators:
- Interactive candlestick charts
- Volume analysis
- Multiple timeframes (Daily, Weekly, Monthly)
- Historical price data visualization

## Getting Started

1. **Select a Dashboard** from the sidebar navigation menu
2. **Choose a Stock** ticker symbol
3. **Configure Parameters** and analyze!

---

⚠️ **Disclaimer**: This is for educational purposes only and should not be considered as financial advice. 
Always do your own research and consult with a financial advisor.
""")

# Add some visual elements
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Fundamentals", "Analysis", "📊")

with col2:
    st.metric("Technical", "Analysis", "📈")

with col3:
    st.metric("Real-time", "Data", "🔄")

