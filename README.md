# Fundamentals Investment Dashboard

A comprehensive Streamlit dashboard for fundamental analysis of stocks, designed for long-term investment decisions (3-5 years).

## Features

- **Interactive Dashboard**: User-friendly interface for analyzing any stock ticker
- **Comprehensive Analysis**: 
  - Historical financial data and trends
  - Growth rate calculations
  - Future price projections
  - Intrinsic value estimation
  - Risk assessment
- **Investment Metrics**:
  - P/E ratios
  - Discount rates
  - Margin of safety
  - Expected returns
- **Visual Charts**: Price projection graphs and data tables
- **Investment Recommendations**: Buy/Hold/Avoid signals based on analysis

## Installation

1. Clone or download this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Create a `.env` file with your SerpAPI key for investor relations links:
```
SERPAPI_KEY=your_serpapi_key_here
```

## Usage

### Running the Dashboard

```bash
streamlit run dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`

### Using the Dashboard

1. **Enter a Ticker**: Input any valid stock symbol (e.g., AAPL, NVDA, TSLA)
2. **Set Parameters**: 
   - Adjust investment timeline (1-10 years)
   - Set margin of safety (5-30%)
3. **Analyze**: Click "Analyze Company" to generate the full report
4. **Review Results**: 
   - Key metrics at the top
   - Buy/Hold/Avoid recommendation
   - Detailed financial analysis in tabs
   - Risk assessment
   - Investment summary

### Running the Original Script

You can also run the original command-line version:

```bash
python report.py
```

## Key Components

- `dashboard.py`: Streamlit web interface
- `report.py`: Original command-line analysis script
- `report_utils.py`: Core analysis functions and calculations

## Investment Methodology

This tool focuses on fundamental analysis for profitable companies using:

- **Discounted Cash Flow (DCF)** modeling
- **Price-to-Earnings (P/E)** ratio analysis
- **Growth rate** projections based on analyst estimates
- **Risk-adjusted discount rates** based on company characteristics
- **Margin of safety** for conservative valuations

## Important Disclaimers

⚠️ **This tool is for educational purposes only and should not be considered as financial advice.**

- Always conduct your own research
- Consult with a qualified financial advisor
- Past performance does not guarantee future results
- All investments carry risk of loss

## Data Sources

- Financial data: Yahoo Finance (via yfinance)
- Analyst estimates: Yahoo Finance Analysis pages
- Company information: Yahoo Finance API

## Technical Requirements

- Python 3.8+
- Internet connection for real-time data
- Modern web browser for Streamlit interface

## Troubleshooting

- **"No data found"**: Check if the ticker symbol is correct
- **"EPS is negative"**: The tool only analyzes profitable companies
- **Connection errors**: Check your internet connection
- **Missing data**: Some companies may not have complete financial data available 