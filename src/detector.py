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
            'trendlines': {'upper': None, 'lower': None},
            'selection_score': -1.0
        }
        
        adaptive_windows = list(range(40, 360, 10))

        valid_results = []
        
        for window in adaptive_windows:
            if len(df) < window: continue
            
            df_slice = df.tail(window).copy()
            
            # dynamic adjustment of the order
            current_order = max(3, self.order if window > 100 else self.order - 2)
            
            # running the detection on the specific window
            original_order = self.order
            self.order = current_order
            result = self._find_pattern_in_window(df_slice)
            self.order = original_order
            
            if result['is_converging'] and result['is_breaking_out']:
                # calculating a quality score that favors high R2 (precision over time)
                # significant bonus for windows that show geometric "cleanliness" (R2 > 0.8)
                quality_bonus = 1.5 if result['r2_high'] > 0.8 else 1.0
                window_weight = 1.2 if window <= 90 else 1.0
                
                result['selection_score'] = result['r2_high'] * window_weight * quality_bonus
                result['used_window'] = window
                valid_results.append(result)

        if valid_results:
            # selecting the window that has the most "correct" geometric structure statistically
            best_result = max(valid_results, key=lambda x: x['selection_score'])
            logger.info(f"Adaptive scan selected window {best_result['used_window']} (R2: {best_result['r2_high']:.2f})")
            
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

        # filtering insignificant extrema points
        high_idx = self._filter_significant_extrema(high_idx, df['High'].values, is_high=True)
        low_idx = self._filter_significant_extrema(low_idx, df['Low'].values, is_high=False)

        if len(high_idx) > self.min_points:
            # we take only the N highest points that create the trend line
            # this prevents low points in the middle from pulling the regression
            high_values = df['High'].values[high_idx]
            threshold = np.percentile(high_values, 30) # filtering out the 30% lowest points from the highs
            high_idx = high_idx[high_values >= threshold]

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

    def _filter_significant_extrema(self, indices: np.ndarray, values: np.ndarray, is_high: bool) -> np.ndarray:
        """
        Filters out insignificant extrema points and keeps only those that define the envelope.
        """
        if len(indices) <= self.min_points:
            return indices

        filtered = []
        # minimum distance between extrema points (based on the original order)
        min_dist = self.order * 2 

        # sorting the points by strength (highest for highs, lowest for lows)
        sorted_indices = sorted(indices, key=lambda idx: values[idx], reverse=is_high)
        
        for idx in sorted_indices:
            # checking if the point is far enough from the points we already selected
            if all(abs(idx - f_idx) > min_dist for f_idx in filtered):
                filtered.append(idx)
        
        # returning the indices in chronological order
        return np.sort(np.array(filtered))