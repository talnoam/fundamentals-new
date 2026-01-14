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
        self.convergence_threshold = config.get('convergence_threshold', 0.1) # Maximum distance at the end.

    def analyze_convergence(self, df: pd.DataFrame) -> dict:
        """
        Analyzes whether the stock chart is in a convergence process.
        """
        if len(df) < 50:
            return {'is_converging': False}

        prices = df['Close'].values
        x_axis = np.arange(len(prices))

        # 1. Finding local extrema points.
        high_idx = argrelextrema(df['High'].values, np.greater, order=self.order)[0]
        low_idx = argrelextrema(df['Low'].values, np.less, order=self.order)[0]

        if len(high_idx) < self.min_points or len(low_idx) < self.min_points:
            return {'is_converging': False}

        # 2. Fitting trend lines (linear regression).
        # Resistance line (highs).
        model_high = LinearRegression().fit(high_idx.reshape(-1, 1), df['High'].values[high_idx])
        r2_high = model_high.score(high_idx.reshape(-1, 1), df['High'].values[high_idx])
        slope_high = model_high.coef_[0]
        intercept_high = model_high.intercept_

        # Support line (lows).
        model_low = LinearRegression().fit(low_idx.reshape(-1, 1), df['Low'].values[low_idx])
        r2_low = model_low.score(low_idx.reshape(-1, 1), df['Low'].values[low_idx])
        slope_low = model_low.coef_[0]
        intercept_low = model_low.intercept_

        # 3. Checking convergence conditions (mathematical conditions).
        # a. The lines must get closer to each other.
        # The upper slope must be smaller than the lower slope (for example, the upper is negative and the lower is positive).
        is_closing = slope_high < slope_low

        # b. Calculating the distance between the lines at the end of the period.
        last_idx = len(prices) - 1
        dist_start = (model_high.predict([[0]]) - model_low.predict([[0]]))[0]
        dist_end = (model_high.predict([[last_idx]]) - model_low.predict([[last_idx]]))[0]
        
        # Has the distance decreased significantly?
        compression = dist_end / dist_start if dist_start != 0 else 1

        # 4. Breakout detection.
        current_price = prices[-1]
        resistance_line = model_high.predict([[last_idx]])[0]
        is_breaking_out = current_price > resistance_line

        is_converging = is_closing and compression < 0.7 # Example: a reduction of at least 30%.

        return {
            'is_converging': is_converging,
            'is_breaking_out': is_breaking_out,
            'r2_high': r2_high,
            'r2_low': r2_low,
            'slopes': (slope_high, slope_low),
            'trendlines': {
                'upper': (slope_high * x_axis + intercept_high),
                'lower': (slope_low * x_axis + intercept_low)
            },
            'compression': compression,
            'score': (1 - compression) * (1 if is_breaking_out else 0.5)
        }