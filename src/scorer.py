import numpy as np
import pandas as pd
from sklearn.metrics import r2_score
import logging

logger = logging.getLogger(__name__)

class ScoringEngine:
    def __init__(self, config: dict):
        self.weights = config.get('weights', {
            'quality': 0.3,
            'compression': 0.3,
            'volume': 0.2,
            'breakout_strength': 0.1,
            'freshness': 0.1
        })
        self.r2_quality_min = config.get('r2_quality_min', 0.5)
        self.breakout_strength_max = config.get('breakout_strength_max', 0.03)
        self.volume_window = config.get('volume_window', 20)
        self.volume_ratio_full_score = config.get('volume_ratio_full_score', 2.0)
        self.breakout_age_scores = self._normalize_age_scores(
            config.get('breakout_age_scores', {1: 1.0, 2: 0.7})
        )
        self.breakout_age_default_score = config.get('breakout_age_default_score', 0.0)
        self.final_score_scale = config.get('final_score_scale', 100.0)
        self.volatility_bonus_scale = config.get('volatility_bonus_scale', 10.0)
        self.annual_trading_days = config.get('annual_trading_days', 252)
        self.max_annual_volatility = config.get('max_annual_volatility', 0.50)

    def _normalize_age_scores(self, scores) -> dict:
        normalized = {}
        for key, value in (scores or {}).items():
            try:
                normalized[int(key)] = float(value)
            except (TypeError, ValueError):
                continue
        return normalized

    def calculate_score(self, df: pd.DataFrame, pattern: dict) -> float:
        """
        Calculates a final score between 0 and 100 for a breakout candidate.
        """
        try:
            # If the stock broke down, we don't want to recommend it at all
            if pattern.get('is_breaking_down', False):
                return 0.0
            
            # If there is no breakout upwards, we can give a very low score or 0
            if not pattern.get('is_breaking_out', False):
                return 0.0

            # 1. Quality metric (R-squared) - how 'clean' the lines are
            # We check how close the extrema points are to the regression lines calculated in Detector
            quality_score = self._calculate_quality(pattern)

            # 2. Compression metric - how close the stock is to the apex of the triangle
            # The more compressed the price, the more violent the breakout is expected to be
            compression_score = 1 - pattern.get('compression', 1)
            compression_score = max(0, min(1, compression_score)) # Normalization

            # 3. Volume metric (Relative Volume)
            # A reliable breakout must come with volume higher than average
            volume_score = self._calculate_volume_score(df)

            # 4. Breakout Strength (Normalization: breakout_strength_max gets a score of 1.0)
            raw_strength = pattern.get('breakout_strength', 0)
            strength_score = 0.0
            if pattern['is_breaking_out'] and self.breakout_strength_max > 0:
                strength_score = max(0, min(1, raw_strength / self.breakout_strength_max))

            # 5. Freshness Score (Bonus for the first day)
            age = pattern.get('breakout_age', 0)
            freshness_score = self.breakout_age_scores.get(age, self.breakout_age_default_score)

            # 6. Momentum/Volatility Bonus
            vol_score = self._calculate_volatility_score(df)

            # Final calculation
            final_score = (
                quality_score * self.weights.get('quality', 0.2) +
                compression_score * self.weights.get('compression', 0.3) +
                volume_score * self.weights.get('volume', 0.3) +
                strength_score * self.weights.get('breakout_strength', 0.1) +
                freshness_score * self.weights.get('freshness', 0.1)
            )
            final_score = (
                (final_score * self.final_score_scale) +
                (vol_score * self.volatility_bonus_scale)
            )

            return round(min(100, final_score), 2)

        except Exception as e:
            logger.error(f"Error in scoring: {e}")
            return 0.0

    def _calculate_quality(self, pattern: dict) -> float:
        """
        Calculates the quality of the trend lines based on the average R² of them.
        """
        # If the Detector didn't return R², we'll use a default value
        r2_high = pattern.get('r2_high', 0)
        if r2_high < self.r2_quality_min:
            return 0.0
        r2_low = pattern.get('r2_low', 0)
        
        # Weighted average of the quality of the lines
        quality = (r2_high + r2_low) / 2
        
        # Validation that the value is within the range [0, 1]
        return max(0, min(1, quality))

    def _calculate_volume_score(self, df: pd.DataFrame) -> float:
        """
        Checks whether the current volume is higher than the average of the last 20 days.
        """
        recent_volume = df['Volume'].values[-1]
        avg_volume = df['Volume'].rolling(window=self.volume_window).mean().values[-1]
        
        if avg_volume == 0: return 0
        
        rel_vol = recent_volume / avg_volume
        # Normalization: if the volume is volume_ratio_full_score * avg, the score is 1
        if self.volume_ratio_full_score <= 0:
            return 0.0
        return float(max(0, min(1, (rel_vol / self.volume_ratio_full_score))))

    def _calculate_volatility_score(self, df: pd.DataFrame) -> float:
        """
        Calculates annualized volatility to identify high-momentum stocks.
        """
        # Calculate daily returns standard deviation
        daily_returns = df['Close'].pct_change().dropna()
        if daily_returns.empty:
            return 0.0
            
        # Annual volatility formula:
        # $\sigma_{annual} = \sigma_{daily} \cdot \sqrt{252}$
        annual_vol = daily_returns.std() * (self.annual_trading_days ** 0.5)

        # Normalization: volatility of max_annual_volatility or higher gets a score of 1.0
        if self.max_annual_volatility <= 0:
            return 0.0
        return float(max(0, min(1, annual_vol / self.max_annual_volatility)))