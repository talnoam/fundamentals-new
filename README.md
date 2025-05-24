# Fundamentals: Company Analysis & Valuation

## Project Description
This project analyzes the fundamentals of publicly traded companies to estimate their future earnings per share (EPS), growth rates, and potential stock prices. It is designed for long-term investment analysis (3-5 years) and focuses on companies that are profitable and potentially undervalued by the market.

## Key Parameters and Calculations

### 1. Discount Rate
The discount rate represents the required rate of return for an investment. It's calculated using a modified Capital Asset Pricing Model (CAPM) approach:

```python
discount_rate = risk_free_rate + (beta * market_risk_premium) + company_risk
```

Components:
- **Risk-free Rate**: Current 10-year Treasury yield (typically 4-5%)
- **Market Risk Premium**: Historical average return of S&P 500 minus risk-free rate (typically 6%)
- **Beta**: Company's volatility relative to market (from Yahoo Finance)
- **Company Risk**: Additional risk factors specific to the company

Company Risk Factors:
- Negative earnings: +2%
- Low profit margins (<5%): +1%
- High debt-to-equity (>1.0): +1%
- Low current ratio (<1.5): +1%
- High beta (>1.5): +1%
- Low beta (<0.8): -1%
- Tech industry: +1%
- Stable industries: -1%
- Small cap: +2%
- Large cap: -1%
- High growth (>20%): +1%
- Negative growth: +2%

### 2. Margin of Safety
The margin of safety provides a buffer against estimation errors and market volatility. It's calculated based on multiple risk factors:

```python
margin_of_safety = base_mos + financial_risk + profitability_risk + market_risk + industry_risk + size_risk + growth_risk
```

Components:
- **Base Margin**: 10%
- **Financial Risk**:
  - Low current ratio (<1.5): +5%
  - High debt-to-equity (>1.0): +5%
  - Low quick ratio (<1.0): +3%
- **Profitability Risk**:
  - Negative earnings: +10%
  - Low profit margins (<5%): +5%
- **Market Risk**:
  - High beta (>1.5): +5%
  - Low beta (<0.8): -3%
- **Industry Risk**:
  - Tech companies: +5%
  - Stable industries: -3%
- **Size Risk**:
  - Small cap: +5%
  - Large cap: -3%
- **Growth Risk**:
  - High growth (>20%): +5%
  - Negative growth: +8%

### 3. Growth Rate
The growth rate is obtained from analyst estimates on Yahoo Finance:
- Scrapes the "Growth Estimates" table
- Uses the "Next Year" growth estimate
- Expressed as a decimal (e.g., 0.15 for 15%)

### 4. EPS (Earnings Per Share)
The EPS is obtained from analyst estimates on Yahoo Finance:
- Scrapes the "Earnings Estimate" table
- Uses the "Avg. Estimate" for next year
- Used as the base for future projections

### 5. Future Price Calculation
Future prices are calculated using:
```python
future_price = eps * pe_ratio
discounted_price = future_price / ((1 + discount_rate) ** n) * (1 - margin_of_safety)
```

Where:
- `eps`: Projected earnings per share
- `pe_ratio`: Price to earnings ratio
- `n`: Number of years into the future
- `discount_rate`: Required rate of return
- `margin_of_safety`: Safety buffer

## Features
- Fetches financial data using Yahoo Finance (`yfinance`)
- Scrapes analyst growth rates and EPS estimates from Yahoo Finance
- Projects future EPS and stock prices using growth rates and P/E ratios
- Discounts future prices to present value with a margin of safety
- Calculates annual and total returns
- Optionally fetches investor relations links for further research

## Setup Instructions
1. **Clone the repository:**
   ```bash
   git clone https://github.com/talnoam/fundamentals.git
   cd fundamentals
   ```
2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage
- Edit `report.py` to set your desired ticker symbol and parameters
- Run the analysis:
  ```bash
  python report.py
  ```
- The script will output:
  - Growth rate and EPS for the next year
  - Projected EPS and stock prices for the next N years
  - Discounted present values and annual returns
  - (Optional) Investor relations link for the company

## Environment Variables
- The project uses a `.env` file to store sensitive information such as API keys (e.g., `SERPAPI_KEY`)
- Example `.env` file:
  ```
  SERPAPI_KEY=your_serpapi_key_here
  ```
- **Security Note:** `.env` is included in `.gitignore` and should never be committed to version control

## Security & Best Practices
- Never share your `.env` file or API keys publicly
- Always use a virtual environment to manage dependencies
- Review and comply with the terms of service for any data providers or APIs you use

## License
This project is for educational and research purposes. Please review the data sources' terms of use before using in production or commercial settings. 