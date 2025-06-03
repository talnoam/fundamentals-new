# fundamentals is an investment company that invests in companies that are undervalued by the market
# this is a long-term investment for 3-5 years
# only for profitable companies

# we are going to analyze the fundamentals of a company and make a report on it
# we will use the balance sheet, income statement, and cash flow statement to analyze the company
# we will use the financial ratios to analyze the company
# we will use the industry average to compare the company
# we will use the company's own historical data to compare the company
# we will use the company's own competitors to compare the company
# we will use the company's own industry to compare the company
# we will use the company's own market to compare the company
# we will use the company's own management to compare the company
# we will use the company's own technology to compare the company
# we will use the company's own research and development to compare the company
# we will use the company's own patents to compare the company
# we will use the company's own trademarks to compare the company
# we will use the company's own copyrights to compare the company
# we will use the company's own licenses to compare the company
# we will use the company's own contracts to compare the company
# we will use the company's own lawsuits to compare the company
# we will use the company's own lawsuits to compare the company

# import the necessary libraries
import yfinance as yf
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
import os
import streamlit as st
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from datetime import datetime, timedelta

from report_utils import (
    get_next_year_growth_rate, 
    estimate_future_eps_df, 
    estimate_future_prices, 
    calculate_returns, 
    get_ir_link_via_google, 
    calculate_discount_rate, 
    get_financial_metrics
)

load_dotenv()
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

def analyze_company(ticker, years_to_estimate=3, margin_of_safety=0.10, ir_required=False):
    """
    Comprehensive analysis of a company for investment purposes.
    
    Args:
        ticker (str): Stock ticker symbol
        years_to_estimate (int): Number of years to project
        margin_of_safety (float): Margin of safety as decimal (e.g., 0.10 for 10%)
        ir_required (bool): Whether to fetch investor relations link
    
    Returns:
        dict: Complete analysis results
    """
    results = {
        'ticker': ticker.upper(),
        'years_to_estimate': years_to_estimate,
        'analysis_date': datetime.now(),
        'error': None,
        'profitable': True
    }
    
    try:
        # Get company info
        stock = yf.Ticker(ticker)
        info = stock.info
        results['company_name'] = info.get('longName', ticker)
        results['company_info'] = info
        
        # Get financial metrics
        actual_values, percentage_changes = get_financial_metrics(ticker)
        results['actual_values'] = actual_values
        results['percentage_changes'] = percentage_changes
        
        # Calculate key metrics
        discount_rate = calculate_discount_rate(ticker)
        results['discount_rate'] = discount_rate
        results['margin_of_safety'] = margin_of_safety
        
        # Get growth rate and EPS
        EPS, GROWTH_RATE = get_next_year_growth_rate(ticker)
        results['eps'] = EPS
        results['growth_rate'] = GROWTH_RATE
        
        # Get P/E ratio and current price
        pe_gaap_ttm = stock.info.get("trailingPE")
        current_price = stock.history(period="1d")['Close'].iloc[0]
        results['pe_ratio'] = pe_gaap_ttm
        results['current_price'] = current_price
        
        # Check if company is profitable
        if pe_gaap_ttm is None:
            epsTrailingTwelveMonths = stock.info.get("epsTrailingTwelveMonths")
            if epsTrailingTwelveMonths and epsTrailingTwelveMonths < 0:
                results['profitable'] = False
                results['error'] = "EPS is negative, the company is not profitable."
                return results
        
        # Calculate future projections
        future_eps_df = estimate_future_eps_df(EPS, GROWTH_RATE, years=years_to_estimate)
        results['future_eps_df'] = future_eps_df
        
        realistic_prices_df = estimate_future_prices(
            future_eps_df,
            pe_gaap_ttm,
            discount_rate,
            margin_of_safety,
            EPS,
            current_price
        )
        results['realistic_prices_df'] = realistic_prices_df
        
        # Calculate returns
        final_price = realistic_prices_df['Discounted Price'].iloc[-1]
        annualized_return = (final_price / current_price) ** (1 / years_to_estimate) - 1
        returns_df, total_return = calculate_returns(realistic_prices_df, current_price)
        
        results['final_price'] = final_price
        results['annualized_return'] = annualized_return
        results['returns_df'] = returns_df
        results['total_return'] = total_return
        results['fair_value_today'] = realistic_prices_df['Discounted Price'].iloc[0]
        
        # Calculate undiscounted fair value (without margin of safety)
        fair_value = realistic_prices_df['Discounted Price'].iloc[1]
        results['fair_value'] = fair_value
        
        # Investment recommendation based on undiscounted fair value
        # This gives a more accurate picture of the stock's true value
        results['valuation_difference'] = ((fair_value / current_price - 1) * 100)

        # More nuanced recommendation system
        if results['valuation_difference'] > 20:
            results['recommendation'] = 'STRONG BUY'
        elif results['valuation_difference'] > 10:
            results['recommendation'] = 'BUY'
        elif results['valuation_difference'] > 0:
            results['recommendation'] = 'WEAK BUY'
        elif results['valuation_difference'] > -10:
            results['recommendation'] = 'HOLD'
        else:
            results['recommendation'] = 'AVOID'
        
        # Risk assessment
        results['risk_factors'] = assess_risk_factors(discount_rate, GROWTH_RATE, pe_gaap_ttm, info)
        
        # Optional investor relations link
        if ir_required:
            results['ir_link'] = get_ir_link_via_google(ticker, SERPAPI_KEY)
            
    except Exception as e:
        results['error'] = str(e)
        results['profitable'] = False
    
    return results

def assess_risk_factors(discount_rate, growth_rate, pe_ratio, company_info):
    """
    Assess risk factors for the investment.
    
    Args:
        discount_rate (float): Calculated discount rate
        growth_rate (float): Expected growth rate
        pe_ratio (float): P/E ratio
        company_info (dict): Company information from yfinance
    
    Returns:
        list: List of risk factor descriptions
    """
    risk_factors = []
    
    if discount_rate > 0.15:
        risk_factors.append("High discount rate indicates elevated risk")
    if growth_rate > 0.3:
        risk_factors.append("Very high growth expectations may be unrealistic")
    if pe_ratio and pe_ratio > 30:
        risk_factors.append("High P/E ratio suggests expensive valuation")
    if company_info.get('beta', 1) > 1.5:
        risk_factors.append("High beta indicates significant market volatility")
    
    return risk_factors

def print_analysis_results(results):
    """
    Print analysis results to console (for command-line usage).
    
    Args:
        results (dict): Analysis results from analyze_company()
    """
    if results['error']:
        print(f"Error analyzing {results['ticker']}: {results['error']}")
        return
    
    print(f"Ticker: {results['ticker']}\n")
    
    print("Actual Values:")
    print(results['actual_values'])
    print("\nPercentage Changes:")
    print(results['percentage_changes'])
    
    print(f'\nDiscount rate: {results["discount_rate"]:.1%}')
    print(f'GROWTH_RATE: {int(results["growth_rate"]*100)}%')
    print(f'EPS: {results["eps"]:.2f}')
    print(f"P/E GAAP (TTM): {results['pe_ratio']}\n")
    
    print(results['returns_df'])
    print(f'\nCurrent price: ${results["current_price"]:.2f}')
    print(f"Intrinsic value (with MOS): ${results['fair_value_today']:.2f}")
    print(f"Annualized Return over {len(results['future_eps_df'])} years: {results['annualized_return']:.2%}")
    print(f"Total Return over {len(results['future_eps_df'])} years: {results['total_return']:.2f}%")
    
    if 'ir_link' in results:
        print(f"Investor Relations link for {results['ticker']}: {results['ir_link']}")

# Command-line execution (when run directly)
if __name__ == "__main__":
    # Configuration
    TICKER = "NVDA"
    years_to_estimate = 3
    margin_of_safety = 0.10
    ir_required = False
    
    # Run analysis
    results = analyze_company(TICKER, years_to_estimate, margin_of_safety, ir_required)
    
    # Print results
    print_analysis_results(results)   

def display_analysis_results(results):
    """
    Display the analysis results in the Streamlit dashboard.
    
    Args:
        results (dict): Analysis results from analyze_company()
    """
    if results['error']:
        st.error(f"❌ Error analyzing {results['ticker']}: {results['error']}")
        if not results['profitable']:
            st.info("💡 Try analyzing a different profitable company.")
        return
    
    # Company header
    st.header(f"📈 {results['company_name']} ({results['ticker']})")
    
    # Display key metrics at the top
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Current Price", f"${results['current_price']:.2f}")
    
    with col2:
        st.metric("Intrinsic Value", f"${results['fair_value_today']:.2f}", 
                 delta=f"{(results['fair_value_today']-results['current_price']):+.1f}%")
    
    with col3:
        st.metric("Annualized Return", f"{results['annualized_return']:.1%}",
                  delta=f"{results['annualized_return']:.1%}")
    
    with col4:
        st.metric("Total Return", f"{results['total_return']:.1f}%",
                  delta=f"{results['total_return']:.1f}%")
    
    # Investment recommendation with more nuanced messaging
    if results['recommendation'] == 'STRONG BUY':
        st.success(f"🟢 **STRONG BUY**: Stock appears significantly undervalued by {abs(results['valuation_difference']):.1f}%")
    elif results['recommendation'] == 'BUY':
        st.success(f"🟢 **BUY**: Stock appears undervalued by {abs(results['valuation_difference']):.1f}%")
    elif results['recommendation'] == 'WEAK BUY':
        st.info(f"🔵 **WEAK BUY**: Stock appears slightly undervalued by {abs(results['valuation_difference']):.1f}%")
    elif results['recommendation'] == 'HOLD':
        st.warning(f"🟡 **HOLD**: Stock appears fairly valued (within 10% of fair value)")
    else:
        st.error(f"🔴 **AVOID**: Stock appears overvalued by {abs(results['valuation_difference']):.1f}%")
    
    st.divider()
    
    # Financial Analysis Section
    st.header("📊 Financial Analysis")
    
    tab1, tab2, tab3 = st.tabs(["Historical Values", "Growth Rates", "Future Projections"])
    
    with tab1:
        st.subheader("Historical Financial Data")
        st.dataframe(results['actual_values'], use_container_width=True)
    
    with tab2:
        st.subheader("Year-over-Year Changes")
        st.dataframe(results['percentage_changes'], use_container_width=True)
    
    with tab3:
        st.subheader("Future Price Projections")
        st.dataframe(results['realistic_prices_df'], use_container_width=True)
    
    st.divider()
    
    # Key Investment Metrics
    st.header("🎯 Key Investment Metrics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Valuation Metrics")
        metrics_data = {
            "Metric": [
                "P/E Ratio (TTM)",
                "Expected Growth Rate",
                "Next Year EPS",
                "Discount Rate",
                "Margin of Safety"
            ],
            "Value": [
                f"{results['pe_ratio']:.2f}" if results['pe_ratio'] else "N/A",
                f"{results['growth_rate']:.1%}",
                f"${results['eps']:.2f}",
                f"{results['discount_rate']:.1%}",
                f"{results['margin_of_safety']:.1%}"
            ]
        }
        st.table(pd.DataFrame(metrics_data))
    
    with col2:
        st.subheader("Company Information")
        info = results['company_info']
        company_info = {
            "Metric": [
                "Market Cap",
                "Industry",
                "Sector",
                "Beta",
                "52 Week High",
                "52 Week Low"
            ],
            "Value": [
                f"${info.get('marketCap', 0):,.0f}" if info.get('marketCap') else "N/A",
                info.get('industry', 'N/A'),
                info.get('sector', 'N/A'),
                f"{info.get('beta', 'N/A'):.2f}" if info.get('beta') else "N/A",
                f"${info.get('fiftyTwoWeekHigh', 0):.2f}" if info.get('fiftyTwoWeekHigh') else "N/A",
                f"${info.get('fiftyTwoWeekLow', 0):.2f}" if info.get('fiftyTwoWeekLow') else "N/A"
            ]
        }
        st.table(pd.DataFrame(company_info))
    
    # Chart for price projections
    st.subheader("📈 Price Projection Chart")
    chart_data = results['realistic_prices_df'].set_index('Year')[['Future Price', 'Discounted Price']]
    st.line_chart(chart_data)
    
    st.divider()
    
    # Risk Assessment
    st.header("⚠️ Risk Assessment")
    
    if results['risk_factors']:
        for risk in results['risk_factors']:
            st.warning(f"⚠️ {risk}")
    else:
        st.success("✅ No major risk factors identified")
    
    # Investment Summary
    st.header("📝 Investment Summary")
    st.write(f"""
    **Company**: {results['company_name']} ({results['ticker']})
    
    **Investment Thesis**: 
    - Current Price: ${results['current_price']:.2f}
    - Estimated Intrinsic Value: ${results['fair_value_today']:.2f}
    - Expected Annual Return: {results['annualized_return']:.1%}
    - Investment Period: {results['years_to_estimate']} years
    
    **Key Assumptions**:
    - P/E Ratio: {results['pe_ratio']:.1f}
    - Growth Rate: {results['growth_rate']:.1%}
    - Discount Rate: {results['discount_rate']:.1%}
    - Margin of Safety: {results['margin_of_safety']:.1%}
    
    **Recommendation**: {results['recommendation']}
    """)
    
    # Optional IR link
    if 'ir_link' in results:
        st.subheader("🔗 Additional Resources")
        st.write(f"[Investor Relations Page]({results['ir_link']})")


# Function to create candlestick chart
def create_candlestick_chart(ticker, years_to_estimate, timeframe):
    try:
        # Calculate the period based on years_to_estimate
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years_to_estimate * 365)
        
        # Download stock data
        stock = yf.Ticker(ticker)
        
        # Get different intervals based on timeframe
        if timeframe == "Daily":
            interval = "1d"
        elif timeframe == "Weekly":
            interval = "1wk"
        else:  # Monthly
            interval = "1mo"
            
        # Download data
        data = stock.history(
            start=start_date,
            end=end_date,
            interval=interval
        )
        
        if data.empty:
            st.error(f"No data available for {ticker}")
            return None
            
        # Create candlestick chart with reduced volume chart height
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,  # Reduced spacing between charts
            subplot_titles=(f'{ticker} Stock Price ({timeframe})', 'Volume'),
            row_heights=[0.8, 0.2]  # 80% for price, 20% for volume
        )
        
        # Add candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name="Price"
            ),
            row=1, col=1
        )
        
        # Add volume chart
        fig.add_trace(
            go.Bar(
                x=data.index,
                y=data['Volume'],
                name="Volume",
                marker_color='rgba(0,150,255,0.6)'
            ),
            row=2, col=1
        )
        
        # Update layout
        fig.update_layout(
            height=600,
            title_text=f"{ticker} Stock Analysis - {timeframe} View",
            xaxis_rangeslider_visible=False,
            showlegend=False
        )
        
        # Update x-axis
        fig.update_xaxes(title_text="Date", row=2, col=1)
        
        # Update y-axis
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating chart: {str(e)}")
        return None