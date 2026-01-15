import numpy as np
import pandas as pd
from scipy.signal import argrelextrema
from sklearn.linear_model import LinearRegression
import logging

logger = logging.getLogger(__name__)

class PatternDetector:
    def __init__(self, config: dict):
        self.order = config.get('extrema_order', 5)  # How many days on each side of each point for it to be considered a peak.
        self.min_points = config.get('min_points', 3) # Minimum points for a trend line.
        self.convergence_threshold = config.get('convergence_threshold', 0.1) # Max distance ratio at the end.
        self.windows = config.get('windows', [60, 90, 120, 160, 252])
        self.weight_start = config.get('trend_weight_start', 1.0)
        self.weight_end = config.get('trend_weight_end', 5.0)
        self.breakout_min_days = config.get('breakout_min_days', 1)
        self.breakout_max_days = config.get('breakout_max_days', 2)
        self.breakdown_confirm_days = config.get('breakdown_confirm_days', 2)

    def analyze_convergence(self, df: pd.DataFrame) -> dict:
        """
        Runs the detection on several time windows and selects the one with the highest R2.
        """
        # Initialize an empty result with all keys to avoid KeyErrors
        best_result = {
            'is_converging': False, 
            'is_breaking_out': False,
            'r2_high': -1.0,
            'breakout_age': 0,
            'trendlines': {'upper': None, 'lower': None}
        }
        
        for window in self.windows:
            if len(df) < window:
                continue
                
            # Cutting the data to the specific window
            df_slice = df.tail(window).copy()
            result = self._find_pattern_in_window(df_slice)
            
            # We select the window with the highest R2 (highest confidence)
            # and only if convergence and breakout were found
            if result['is_converging'] and result['is_breaking_out']:
                if result['r2_high'] > best_result['r2_high']:
                    best_result = result
                    best_result['used_window'] = window
        
        return best_result

    def _find_pattern_in_window(self, df: pd.DataFrame) -> dict:
        """
        Analyzes whether the stock chart is in a convergence process.
        """
        prices = df['Close'].values
        x_axis = np.arange(len(prices))

        # 1. Finding local extrema points.
        high_idx = argrelextrema(df['High'].values, np.greater, order=self.order)[0]
        low_idx = argrelextrema(df['Low'].values, np.less, order=self.order)[0]

        if len(high_idx) < self.min_points or len(low_idx) < self.min_points:
            return {'is_converging': False, 'is_breaking_out': False, 'r2_high': -1}

        # 2. Fitting trend lines (linear regression).

        # Resistance line (highs)
        weights = np.linspace(self.weight_start, self.weight_end, len(high_idx))
        model_high = LinearRegression().fit(high_idx.reshape(-1, 1), df['High'].values[high_idx], sample_weight=weights)
        r2_high = model_high.score(high_idx.reshape(-1, 1), df['High'].values[high_idx])

        slope_high = model_high.coef_[0]
        intercept_high = model_high.intercept_
        upper_trendline = pd.Series(slope_high * x_axis + intercept_high, index=df.index)

        # Support line (lows).
        model_low = LinearRegression().fit(low_idx.reshape(-1, 1), df['Low'].values[low_idx])
        r2_low = model_low.score(low_idx.reshape(-1, 1), df['Low'].values[low_idx])
        slope_low = model_low.coef_[0]
        intercept_low = model_low.intercept_
        lower_trendline = pd.Series(slope_low * x_axis + intercept_low, index=df.index)

        # 3. Checking convergence and compression
        first_extrema_idx = int(min(high_idx[0], low_idx[0]))
        dist_start = upper_trendline.iloc[first_extrema_idx] - lower_trendline.iloc[first_extrema_idx]
        dist_end = upper_trendline.iloc[-1] - lower_trendline.iloc[-1]
        compression = float(dist_end / dist_start) if dist_start > 0 else 1.0

        is_converging = (slope_high < slope_low) and (compression < self.convergence_threshold)

        # 4. Breakout detection (vectorized)
        # Comparing all prices to the trend line in one go
        is_above = (prices > upper_trendline.values)
        consecutive_above = 0
        for val in reversed(is_above):
            if val:
                consecutive_above += 1
            else:
                break
        
        # Definition: a relevant breakout is only one that has exactly 1 or 2 days above the line
        is_breaking_out = self.breakout_min_days <= consecutive_above <= self.breakout_max_days

        # Detection of a breakdown
        confirm_days = min(len(prices), max(1, self.breakdown_confirm_days))
        is_breaking_down = all(
            prices[-offset] < lower_trendline.iloc[-offset]
            for offset in range(1, confirm_days + 1)
        )

        return {
            'is_converging': is_converging,
            'is_breaking_out': is_breaking_out,
            'is_breaking_down': is_breaking_down,
            'breakout_age': int(consecutive_above),
            'breakout_strength': float((prices[-1] / upper_trendline.iloc[-1]) - 1),
            'r2_high': r2_high,
            'r2_low': r2_low,
            'trendlines': {'upper': upper_trendline, 'lower': lower_trendline},
            'compression': compression
        }