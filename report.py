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
import numpy as np
from dotenv import load_dotenv
import os

from report_utils import get_next_year_growth_rate, estimate_future_eps_df, estimate_future_prices, calculate_returns, get_ir_link_via_google, calculate_discount_rate

load_dotenv()
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

ir_required = False

TICKER = "UBER"
years_to_estimate = 3 # the number of years to estimate the future growth of the company
discount_rate = calculate_discount_rate(TICKER) # the yield that we expect from the company's stock per year
print('Discount rate: ', discount_rate)
margin_of_safety = 0.10 # the margin of safety that we want to have

EPS, GROWTH_RATE = get_next_year_growth_rate(TICKER)  # expected growth rate of the company for the next year

print('GROWTH_RATE: ', str(int(GROWTH_RATE*100))+'%')
print('EPS: ', round(EPS, 2))

future_eps_df = estimate_future_eps_df(EPS, GROWTH_RATE, years=years_to_estimate)

pe_gaap_ttm = yf.Ticker(TICKER).info.get("trailingPE")
print(f"P/E GAAP (TTM) for {TICKER}:", pe_gaap_ttm)

if pe_gaap_ttm is None:
    epsTrailingTwelveMonths = yf.Ticker(TICKER).info.get("epsTrailingTwelveMonths")
    if epsTrailingTwelveMonths<0:
        print("EPS is negative, the company is not profitable.")
        print("Choose a different company to evaluate.")

else:
    realistic_prices_df = estimate_future_prices(
        future_eps_df,
        pe_gaap_ttm,
        discount_rate,
        margin_of_safety
    )

    current_price = yf.Ticker(TICKER).history(period="1d")['Close'].iloc[0]
    final_price = realistic_prices_df['Discounted Price'].iloc[-1]
    annualized_return = (final_price / current_price) ** (1 / years_to_estimate) - 1
    returns_df, total_return = calculate_returns(realistic_prices_df, current_price)
    current_row = {
        "Year": datetime.now().year,
        "Estimated EPS": EPS,
        "Future Price": current_price,
        "Discounted Price": current_price*(1 - margin_of_safety),
        "Annual Return (%)": np.nan
    }
    current_df = pd.DataFrame([current_row])
    returns_df = pd.concat([current_df, returns_df], ignore_index=True)
    print(returns_df)
    print(f"Annualized Return over {years_to_estimate} years: {annualized_return:.2%}")
    print(f"Total Return over {years_to_estimate} years: {total_return:.2f}%")

    if ir_required:
        ir_link = get_ir_link_via_google(TICKER, SERPAPI_KEY)
        print(f"Investor Relations link for {TICKER}: {ir_link}")   
