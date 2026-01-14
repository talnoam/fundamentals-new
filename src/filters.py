import pandas as pd
import yfinance as yf
import logging
import numpy as np
from typing import List

logger = logging.getLogger(__name__)

class FilterEngine:
    def __init__(self, config: dict):
        self.min_market_cap = config.get('min_market_cap', 2e9)  # default 2 billion
        self.sma_period = config.get('sma_period', 150)
        self.slope_threshold = config.get('max_slope', 0.0) # negative slope is still/strong (depending on the strategy)
        self.batch_size = config.get('batch_size', 50)

    def apply_coarse_filters(self, tickers: List[str]) -> List[str]:
        """
        receives a list of tickers and returns only those that passed the primary filter.
        """
        logger.info(f"Applying coarse filters to {len(tickers)} tickers...")
        passed_tickers = []

        # split into batches to avoid overloading the API
        for i in range(0, len(tickers), self.batch_size):
            batch = tickers[i : i + self.batch_size]
            try:
                # 1. fetch historical price data for slope calculation
                # we fetch enough data to calculate SMA200 and the slope of it
                data = yf.download(batch, period="300d", interval="1d", group_by='ticker', threads=True, progress=False)
                
                for ticker in batch:
                    if ticker not in data.columns.get_level_values(0):
                        continue
                        
                    df = data[ticker].dropna()
                    if len(df) < self.sma_period + 20:
                        continue

                    # check market cap (optional - requires additional call or use of fast_info)
                    # in yfinance new, fast_info is very fast
                    ticker_obj = yf.Ticker(ticker)
                    try:
                        mcap = ticker_obj.fast_info['marketCap']
                        if mcap < self.min_market_cap:
                            continue
                    except:
                        continue

                    # 2. calculate the moving average slope (SMA Slope)
                    if self._is_trend_bullish(df):
                        passed_tickers.append(ticker)

            except Exception as e:
                logger.error(f"Error processing batch starting with {batch[0]}: {e}")

        logger.info(f"Filtering complete. {len(passed_tickers)} tickers passed.")
        return passed_tickers

    def _is_trend_bullish(self, df: pd.DataFrame) -> bool:
        """
        Checks two accumulated conditions:
        1. The current price is above the 150-day SMA.
        2. The slope of the SMA is 0 or positive (not decreasing).
        """
        close = df['Close']
        sma = close.rolling(window=self.sma_period).mean()
        
        # Checking that there is enough data for the calculation
        recent_sma = sma.dropna().tail(20)
        if len(recent_sma) < 20:
            return False
            
        # 1. Checking the position: the last closing price (close) is above the last SMA
        current_price = close.iloc[-1]
        current_sma = sma.iloc[-1]
        
        if current_price <= current_sma:
            return False

        # 2. Checking the slope (Regression on SMA)
        # Normalizing the SMA so the slope is limited by the price
        x = np.arange(len(recent_sma))
        y = recent_sma.values / recent_sma.values[0]
        slope, _ = np.polyfit(x, y, 1)
        
        # The condition: slope is positive or zero
        return slope >= self.slope_threshold