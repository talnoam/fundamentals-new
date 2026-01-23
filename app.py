import streamlit as st
from src.version_manager import VersionManager 

# Configure Streamlit page
st.set_page_config(
    page_title="Investment Analysis Dashboards",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# display the version in the sidebar
VersionManager.display_version_sidebar()   

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
- SMA indicators (20, 50, 150, 200 periods)
- Automatic support and resistance levels
- Historical price data visualization (1-10 years)

### 📊 Report Charts Dashboard
Analyze previously generated report charts:
- Browse saved report charts from reports/charts
- Filter by ticker and report date
- Interactive zoom, pan, and hover analysis

### 🌍 Market Analysis Dashboard
Comprehensive market indicators and economic data analysis:
- Multiple market indicators (Bitcoin, S&P 500, NASDAQ, Dow Jones, etc.)
- Compare multiple indicators on the same chart
- Flexible time periods (1 Day, 7 Days, 1 Month, 6 Months, Year to Date, or Custom)
- Normalization option for comparing indicators with different price scales
- Commodities (Gold, Silver, Crude Oil)
- Economic indicators (VIX, Treasury yields, Dollar Index)

## Getting Started

1. **Select a Dashboard** from the sidebar navigation menu
2. **Choose a Stock/Indicator** ticker symbol or market indicator
3. **Configure Parameters** and analyze!

---

⚠️ **Disclaimer**: This is for educational purposes only and should not be considered as financial advice. 
Always do your own research and consult with a financial advisor.
""")

# Add some visual elements
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Fundamentals", "Analysis", "📊")

with col2:
    st.metric("Technical", "Analysis", "📈")

with col3:
    st.metric("Market", "Analysis", "🌍")

with col4:
    st.metric("Real-time", "Data", "🔄")

with col5:
    st.metric("Report", "Charts", "📊")

