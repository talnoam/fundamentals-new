import numpy as np
import pandas as pd
from sklearn.metrics import r2_score
import logging

logger = logging.getLogger(__name__)

class ScoringEngine:
    def __init__(self, config: dict):
        self.weights = config.get('weights', {
            'quality': 0.4,
            'compression': 0.4,
            'volume': 0.2
        })

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

            # Final calculation
            final_score = (
                quality_score * self.weights['quality'] +
                compression_score * self.weights['compression'] +
                volume_score * self.weights['volume']
            ) * 100

            return round(final_score, 2)

        except Exception as e:
            logger.error(f"Error in scoring: {e}")
            return 0.0

    def _calculate_quality(self, pattern: dict) -> float:
        """
        Calculates the quality of the trend lines based on the average R² of them.
        """
        # If the Detector didn't return R², we'll use a default value
        r2_high = pattern.get('r2_high', 0)
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
        avg_volume = df['Volume'].rolling(window=20).mean().values[-1]
        
        if avg_volume == 0: return 0
        
        rel_vol = recent_volume / avg_volume
        # Normalization: if the volume is double the average, the score is 1. If it's half - 0.25.
        return float(max(0, min(1, (rel_vol / 2))))