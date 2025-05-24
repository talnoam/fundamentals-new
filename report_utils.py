# Add these imports at the top of your file
import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
from datetime import datetime
from serpapi import GoogleSearch
import yfinance as yf

def get_next_year_growth_rate(ticker):
    """
    Scrapes Yahoo Finance's Analysis page for a given ticker to extract:
    - The expected EPS (Earnings Per Share) for the next year (from the "Earnings Estimate" table).
    - The expected growth rate for the next year (from the "Growth Estimates" table).
    
    Returns:
        eps (float): Analyst consensus EPS estimate for next year.
        growth_rate (float): Expected EPS growth rate for next year (as a decimal, e.g., 0.12 for 12%).
    """
    url = f"https://finance.yahoo.com/quote/{ticker}/analysis"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # Find all tables
    growth_table = soup.find_all("table")[5]
    growth_df = pd.read_html(StringIO(str(growth_table)))[0]
    growth_rate = float(growth_df[growth_df['Unnamed: 0'] == ticker]['Next Year'].iloc[0].strip('%'))/100

    eps_table = soup.find_all("table")[0]
    eps_df = pd.read_html(StringIO(str(eps_table)))[0]
    eps = eps_df[eps_df['Currency in USD'] == 'Avg. Estimate'][eps_df.columns[-1]].iloc[0]

    return eps, growth_rate

def estimate_future_eps_df(current_eps, growth_rate, years=5, start_year=None):
    """
    Projects future EPS (Earnings Per Share) for a given number of years using compound growth.
    Formula: EPS_n = current_eps * (1 + growth_rate)^(n+1)
    
    Args:
        current_eps (float): The base EPS to start projections from (typically next year's EPS).
        growth_rate (float): Expected annual EPS growth rate (as a decimal).
        years (int): Number of years to project.
        start_year (int, optional): The first year of projection (defaults to next calendar year).
    
    Returns:
        pd.DataFrame: DataFrame with columns 'Year' and 'Estimated EPS'.
    """
    if start_year is None:
        start_year = datetime.now().year + 1  # Next year as the starting year
    data = {
        "Year": [start_year + n for n in range(years)],
        "Estimated EPS": [current_eps * (1 + growth_rate) ** (n + 1) for n in range(years)]
    }
    return pd.DataFrame(data)

def estimate_future_prices(future_eps_df, pe_ratio, discount_rate, margin_of_safety, current_eps, current_price):
    """
    Estimates the future stock price for each projected year using the estimated EPS and a given P/E ratio,
    then discounts each future price to present value using a discount rate and applies a margin of safety.
    Includes the current year in the calculations.
    
    Formula:
        Future Price = Estimated EPS * P/E Ratio
        Discounted Price = Future Price / (1 + discount_rate)^n * (1 - margin_of_safety)
    
    Args:
        future_eps_df (pd.DataFrame): DataFrame with 'Year' and 'Estimated EPS'.
        pe_ratio (float): Assumed P/E ratio for future valuation.
        discount_rate (float): Annual discount rate (as a decimal).
        margin_of_safety (float): Margin of safety to apply (as a decimal).
    
    Returns:
        pd.DataFrame: DataFrame with columns 'Year', 'Estimated EPS', 'Future Price', 'Discounted Price'.
    """
    results = []
    current_year = datetime.now().year
    
    # Add current year first
    current_present_value = current_price * (1 - margin_of_safety)  # No discount for current year
    
    results.append({
        "Year": current_year,
        "Estimated EPS": current_eps,
        "Future Price": current_price,
        "Discounted Price": current_present_value
    })

    # Add future years
    for i, row in future_eps_df.iterrows():
        year = row['Year']
        eps = row['Estimated EPS']
        n = i + 1  # years into the future
        future_price = eps * pe_ratio
        present_value = future_price / ((1 + discount_rate) ** n) * (1 - margin_of_safety)
        results.append({
            "Year": year,
            "Estimated EPS": eps,
            "Future Price": future_price,
            "Discounted Price": present_value
        })
    return pd.DataFrame(results)

def calculate_returns(realistic_prices_df, current_price):
    """
    Calculates the annual return (%) for each projected year based on the change in discounted price,
    and the total return (%) over the entire period.
    
    Annual Return for year n:
        (Discounted Price_n - Discounted Price_{n-1}) / Discounted Price_{n-1} * 100
    
    Total Return:
        (Final Discounted Price - Current Price) / Current Price * 100
    
    Args:
        realistic_prices_df (pd.DataFrame): DataFrame with 'Discounted Price' for each year.
        current_price (float): The current stock price.
    
    Returns:
        tuple: (DataFrame with added 'Annual Return (%)' column, total return as a percentage)
    """
    df = realistic_prices_df.copy()
    # Insert current price as the starting point
    prices = [current_price] + df['Discounted Price'].tolist()
    returns = []
    for i in range(1, len(prices)):
        annual_return = (prices[i] - prices[i-1]) / prices[i-1] * 100
        returns.append(annual_return)
    df['Annual Return (%)'] = returns
    total_return = (prices[-1] - prices[0]) / prices[0] * 100
    return df, total_return

def calculate_discount_rate(ticker):
    """
    Automatically calculates an appropriate discount rate for a company based on:
    1. Company's beta (market risk)
    2. Financial health metrics
    3. Industry characteristics
    4. Market conditions
    """
    info = yf.Ticker(ticker).info
    
    # Base components
    # Get the 10-year Treasury yield
    treasury = yf.Ticker("^TNX")  # Symbol for 10-year Treasury yield
    current_yield = treasury.info.get('regularMarketPrice', 4.0)
    risk_free_rate = current_yield / 100  # Convert percentage to decimal

    # Get S&P 500 data
    sp500 = yf.Ticker("^GSPC")
    # Calculate 10-year average return
    hist = sp500.history(period="10y")
    avg_return = (hist['Close'].iloc[-1] / hist['Close'].iloc[0]) ** (1/10) - 1
    # Calculate market risk premium
    mrp = avg_return - risk_free_rate
    # Ensure reasonable bounds (3% to 8%)
    market_risk_premium = max(0.03, min(0.08, mrp))  # Historical market risk premium
    
    # Get company beta, default to 1.0 if not available
    beta = info.get('beta', 1.0)
    
    # Company-specific risk factors
    company_risk = 0.0
    
    # 1. Profitability risk
    if info.get('trailingPE') is None:  # Negative earnings
        company_risk += 0.02
    elif info.get('profitMargins', 0) < 0.05:  # Low profit margins
        company_risk += 0.01
    
    # 2. Financial health risk
    if info.get('debtToEquity', 0) > 1.0:  # High debt
        company_risk += 0.01
    if info.get('currentRatio', 2) < 1.5:  # Low current ratio
        company_risk += 0.01
    
    # 3. Market risk (beta)
    if beta > 1.5:  # High beta
        company_risk += 0.01
    elif beta < 0.8:  # Low beta
        company_risk -= 0.01
    
    # 4. Industry risk
    industry = info.get('industry', '').lower()
    if any(tech in industry for tech in ['software', 'technology', 'internet']):
        company_risk += 0.01  # Tech companies typically have higher risk
    elif any(stable in industry for stable in ['utility', 'consumer defensive', 'healthcare']):
        company_risk -= 0.01  # More stable industries
    
    # 5. Size risk
    market_cap = info.get('marketCap', 0)
    if market_cap < 1e9:  # Small cap
        company_risk += 0.02
    elif market_cap > 1e11:  # Large cap
        company_risk -= 0.01
    
    # 6. Growth risk
    if info.get('revenueGrowth', 0) > 0.2:  # High growth
        company_risk += 0.01
    elif info.get('revenueGrowth', 0) < 0:  # Negative growth
        company_risk += 0.02
    
    # Calculate final discount rate using CAPM-like approach
    discount_rate = risk_free_rate + (beta * market_risk_premium) + company_risk
    
    # Ensure discount rate is within reasonable bounds (8% to 20%)
    discount_rate = max(0.08, min(0.20, discount_rate))
    
    return discount_rate


def get_ir_link_via_google(ticker, api_key):
    query = f"{ticker} investor relations"
    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    if "organic_results" in results and results["organic_results"]:
        return results["organic_results"][0]["link"]
    else:
        return "Not found"


