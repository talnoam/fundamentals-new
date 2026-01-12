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
        self.slope_threshold = config.get('max_slope', -0.05) # negative slope is still/strong (depending on the strategy)
        self.batch_size = config.get('batch_size', 100)

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
                    if self._is_slope_negative(df):
                        passed_tickers.append(ticker)

            except Exception as e:
                logger.error(f"Error processing batch starting with {batch[0]}: {e}")

        logger.info(f"Filtering complete. {len(passed_tickers)} tickers passed.")
        return passed_tickers

    def _is_slope_negative(self, df: pd.DataFrame) -> bool:
        """
        calculates the slope of the SMA150 in the last 20 days.
        """
        close = df['Close']
        sma = close.rolling(window=self.sma_period).mean()
        
        # take the last 20 days of the SMA to measure the slope
        recent_sma = sma.dropna().tail(20)
        if len(recent_sma) < 20:
            return False
            
        # simple linear regression to find the slope (normalize by price so the slope is in percentage)
        x = np.arange(len(recent_sma))
        y = recent_sma.values / recent_sma.values[0] # normalize
        slope, _ = np.polyfit(x, y, 1)
        
        return slope < self.slope_threshold