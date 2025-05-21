# Fundamentals: Company Analysis & Valuation

## Project Description
This project analyzes the fundamentals of publicly traded companies to estimate their future earnings per share (EPS), growth rates, and potential stock prices. It is designed for long-term investment analysis (3-5 years) and focuses on companies that are profitable and potentially undervalued by the market.

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
- Edit `report.py` to set your desired ticker symbol and parameters.
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
- The project uses a `.env` file to store sensitive information such as API keys (e.g., `SERPAPI_KEY`).
- Example `.env` file:
  ```
  SERPAPI_KEY=your_serpapi_key_here
  ```
- **Security Note:** `.env` is included in `.gitignore` and should never be committed to version control.

## Security & Best Practices
- Never share your `.env` file or API keys publicly.
- Always use a virtual environment to manage dependencies.
- Review and comply with the terms of service for any data providers or APIs you use.

## License
This project is for educational and research purposes. Please review the data sources' terms of use before using in production or commercial settings. 