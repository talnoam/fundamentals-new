import pandas as pd
import yfinance as yf
import logging
import numpy as np
from typing import List, Optional

logger = logging.getLogger(__name__)

class FilterEngine:
    def __init__(self, config: dict, data_engine=None):
        self.min_market_cap = config.get('min_market_cap', 2e9)  # default 2 billion
        self.sma_period = config.get('sma_period', 150)
        self.slope_threshold = config.get('max_slope', 0.0) # negative slope is still/strong (depending on the strategy)
        self.batch_size = config.get('batch_size', 50)
        self.data_engine = data_engine  # Optional DataEngine for cache usage
        self.use_cache = data_engine is not None

    def _check_market_cap(self, ticker: str) -> bool:
        """
        Checks if ticker meets minimum market cap requirement.
        Returns True if market cap check passes, False otherwise.
        """
        try:
            ticker_obj = yf.Ticker(ticker)
            mcap = ticker_obj.fast_info['marketCap']
            return mcap >= self.min_market_cap
        except Exception:
            # Market cap unavailable or error - skip this ticker
            return False

    def _process_ticker(self, ticker: str, df: pd.DataFrame) -> bool:
        """
        Processes a single ticker through all filter criteria.
        Returns True if ticker passes all filters, False otherwise.
        """
        # Check if we have enough data (need at least sma_period + 20 days)
        if df.empty or len(df) < self.sma_period + 20:
            logger.debug(f"Insufficient data for {ticker}: {len(df)} rows")
            return False

        # Check market cap
        if not self._check_market_cap(ticker):
            return False

        # Calculate the moving average slope (SMA Slope)
        return self._is_trend_bullish(df)

    def apply_coarse_filters(self, tickers: List[str]) -> List[str]:
        """
        receives a list of tickers and returns only those that passed the primary filter.
        Now uses cached data when available to avoid unnecessary API calls.
        """
        logger.info(f"Applying coarse filters to {len(tickers)} tickers...")
        passed_tickers = []

        if self.use_cache:
            # Use cached data approach - process tickers individually using cache
            logger.info("Using cached data when available to minimize API calls...")
            for ticker in tickers:
                try:
                    # Try to get data from cache first (DataEngine handles cache logic)
                    df = self.data_engine.fetch_historical_data(ticker, force_refresh=False)
                    
                    if self._process_ticker(ticker, df):
                        passed_tickers.append(ticker)

                except Exception as e:
                    logger.debug(f"Error processing {ticker}: {e}")
                    continue
        else:
            # Fallback to batch download approach (original behavior)
            logger.info("Using batch download (no cache available)...")
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
                        
                        if self._process_ticker(ticker, df):
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