# Stock Scanner Selection Logic: How the Top 10 Tickers Are Chosen

## Overview

The stock scanner employs a multi-stage filtering and scoring pipeline to identify the most promising breakout candidates from a universe of tickers (S&P 500, NASDAQ, and Dow Jones). The process systematically narrows down thousands of stocks to the top 10 candidates that exhibit the strongest technical patterns and fundamental characteristics.

---

## Stage 1: Coarse Filtering (Initial Screening)

### Purpose
Eliminate stocks that fail basic fundamental and trend requirements before performing computationally expensive pattern analysis.

### Filter Criteria

#### 1. Market Capitalization Filter
- **Requirement**: Minimum market capitalization of $2 billion
- **Rationale**: Filters out micro-cap stocks that may have liquidity issues, higher volatility, and less reliable data quality
- **Algorithm**: Direct comparison of market cap value against threshold

#### 2. Data Sufficiency Check
- **Requirement**: At least 170 days of historical price data (150-day SMA period + 20 days buffer)
- **Rationale**: Ensures sufficient data for meaningful trend analysis and moving average calculations
- **Algorithm**: Simple length check on historical data series

#### 3. Trend Direction Filter
- **Requirement**: Stock must be in a bullish trend state
- **Rationale**: Focuses on stocks with upward momentum, avoiding declining trends

**Two-Part Trend Validation:**

**Part A - Price Position:**
- Current closing price must be above the 150-day Simple Moving Average (SMA)
- Formula: `Current_Price > SMA_150`
- This ensures the stock is trading above its long-term average, indicating positive momentum

**Part B - SMA Slope:**
- The slope of the 150-day SMA over the last 20 days must be non-negative (≥ 0)
- **Algorithm**: 
  1. Extract the last 20 SMA values
  2. Normalize the SMA series by dividing by the first value: `y_normalized = SMA_values / SMA_values[0]`
  3. Fit a linear regression: `slope = polyfit(x, y_normalized, degree=1)`
  4. Check: `slope ≥ 0`
- **Rationale**: A non-negative slope indicates the moving average is flat or rising, confirming the trend is not deteriorating

### Output
A reduced list of tickers that pass all coarse filters, typically reducing the universe by 60-80%.

---

## Stage 2: Pattern Detection (Convergence Triangle Analysis)

### Purpose
Identify stocks exhibiting converging trend lines (triangle/wedge patterns) with recent breakouts above the upper trendline.

### Adaptive Window Scanning

The system analyzes multiple time windows to find the optimal pattern, recognizing that different stocks form triangles over different periods.

**Window Range**: 40 to 360 days, in 10-day increments (33 different windows tested per stock)

**Rationale**: 
- Short windows (40-90 days) capture recent, tight consolidations
- Medium windows (100-200 days) capture intermediate-term patterns
- Long windows (250-360 days) capture major multi-month consolidations

### Pattern Detection Algorithm (Per Window)

#### Step 1: Extrema Identification

**Local Peak Detection:**
- Uses relative extrema algorithm with order parameter (default: 5)
- A point is a peak if it's the highest value within 5 days on each side
- **Formula**: For each point `i`, check if `High[i] > High[i±k]` for all `k` in [1, 5]

**Local Trough Detection:**
- Similar algorithm for lows: a point is a trough if it's the lowest value within 5 days on each side
- **Formula**: For each point `i`, check if `Low[i] < Low[i±k]` for all `k` in [1, 5]

**Dynamic Order Adjustment:**
- For windows ≤ 100 days: order = 3 (more sensitive, finds more extrema)
- For windows > 100 days: order = 5 (less sensitive, finds significant extrema only)
- **Rationale**: Shorter windows need more extrema points to form meaningful lines; longer windows naturally have more data points

#### Step 2: Extrema Filtering

**Significance Filtering:**
- Removes extrema that are too close together (minimum distance = 2 × order)
- For peaks: sorts by height (highest first), keeps only those spaced sufficiently
- For troughs: sorts by depth (lowest first), keeps only those spaced sufficiently
- **Rationale**: Prevents noise from creating false trend lines; ensures extrema represent meaningful price action

**High Point Pruning:**
- If more than minimum points exist for upper trendline:
  - Calculates 30th percentile of high extrema values
  - Removes the bottom 30% of high points
- **Rationale**: Focuses on the most significant resistance levels, preventing minor peaks from distorting the trendline

**Minimum Points Requirement:**
- Must have at least 3 extrema points for both upper and lower trendlines
- **Rationale**: Requires minimum data points for statistically meaningful linear regression

#### Step 3: Trendline Fitting (Linear Regression)

**Upper Trendline (Resistance):**
- Fits linear regression through high extrema points
- Uses **weighted regression** with time-based weights
- **Weight Formula**: `weight[i] = weight_start + (weight_end - weight_start) × (i / (n-1))`
  - Default: weights increase linearly from 1.0 (oldest) to 5.0 (newest)
- **Rationale**: Recent extrema are more relevant than old ones; weighting emphasizes recent price action
- **Regression Model**: `High = slope_high × time_index + intercept_high`
- **Quality Metric**: Calculates R² (coefficient of determination) to measure how well the line fits the data
  - **R² Formula**: `R² = 1 - (SS_res / SS_tot)`
  - Where `SS_res` = sum of squared residuals, `SS_tot` = total sum of squares
  - R² ranges from 0 to 1; higher values indicate better fit

**Lower Trendline (Support):**
- Fits linear regression through low extrema points
- Uses unweighted regression (all points equally important)
- **Regression Model**: `Low = slope_low × time_index + intercept_low`
- **Quality Metric**: Calculates R² for lower trendline fit

#### Step 4: Convergence Validation

**Compression Calculation:**
- Measures how much the triangle has narrowed
- **Formula**: `compression = distance_end / distance_start`
  - `distance_start` = upper_trendline[start_idx] - lower_trendline[start_idx]
  - `distance_end` = upper_trendline[end_idx] - lower_trendline[end_idx]
- Compression < 1.0 indicates narrowing (convergence)
- Compression = 1.0 indicates parallel lines (no convergence)
- Compression > 1.0 indicates widening (divergence)

**Convergence Condition:**
- **Requirement**: `slope_high < slope_low` AND `compression < convergence_threshold` (default: 0.7)
- **Rationale**: 
  - Upper line must be declining (or less steep than lower line)
  - Lower line must be rising (or less steep than upper line)
  - The gap between lines must have narrowed significantly (compression < 70% of original)

#### Step 5: Breakout Detection

**Breakout Age Calculation:**
- Counts consecutive days where closing price is above upper trendline
- Scans backwards from most recent day
- **Breakout Age** = number of consecutive days above the line (1 or 2 days)

**Breakout Validation:**
- **Requirement**: Breakout age must be between 1 and 2 days (inclusive)
- **Rationale**: 
  - 1-2 days indicates a fresh breakout (not too old, not too new)
  - Older breakouts (>2 days) may have already moved significantly
  - Same-day breakouts may be false signals

**Breakout Strength:**
- **Formula**: `breakout_strength = (current_price / upper_trendline_value) - 1`
- Measures how far above the trendline the price has moved
- Higher values indicate stronger breakout momentum

**Breakdown Detection:**
- Checks if price has broken below lower trendline
- **Requirement**: Price must be below lower trendline for at least 2 consecutive days
- If breakdown detected, stock is immediately disqualified (score = 0)

#### Step 6: Window Selection

For each window that produces a valid converging pattern with breakout:

**Selection Score Calculation:**
- **Base Score**: `R²_high` (quality of upper trendline fit)
- **Quality Bonus**: If `R²_high > 0.8`, multiply by 1.5
  - **Rationale**: Exceptionally clean patterns deserve premium
- **Window Weight**: If `window ≤ 90 days`, multiply by 1.2
  - **Rationale**: Shorter patterns are often more actionable (recent consolidation)
- **Final Selection Score**: `R²_high × quality_bonus × window_weight`

**Best Window Selection:**
- Among all valid windows, selects the one with highest selection score
- **Rationale**: Chooses the time frame that shows the cleanest, most statistically significant pattern

### Pattern Detection Output

For each ticker, returns:
- `is_converging`: Boolean indicating triangle pattern detected
- `is_breaking_out`: Boolean indicating recent breakout above upper line
- `r2_high`: R² value for upper trendline (0 to 1)
- `r2_low`: R² value for lower trendline (0 to 1)
- `breakout_age`: Days since breakout (1 or 2)
- `breakout_strength`: Percentage above trendline
- `compression`: Ratio of end distance to start distance
- `trendlines`: Upper and lower trendline values

---

## Stage 3: Quality Gate

### Purpose
Eliminate low-quality patterns before expensive scoring calculations.

### Requirements
1. **Pattern must be converging**: `is_converging = True`
2. **Breakout must be detected**: `is_breaking_out = True`
3. **Minimum R² quality**: `r2_high ≥ 0.5`
   - **Rationale**: R² < 0.5 indicates poor trendline fit; pattern is unreliable

### Output
Only tickers passing all three requirements proceed to scoring.

---

## Stage 4: Scoring Engine (Multi-Factor Ranking)

### Purpose
Calculate a composite score (0-100) that ranks candidates by investment attractiveness.

### Score Components

#### Component 1: Quality Score (Weight: 20%)

**Definition**: Measures the statistical reliability of the trendline fits.

**Calculation:**
- **Formula**: `quality = (r2_high + r2_low) / 2`
- If `r2_high < 0.5`, quality score = 0 (disqualifies pattern)
- **Normalization**: Clamped to [0, 1] range

**Rationale**: 
- Higher R² values indicate extrema points closely follow the regression lines
- Average of both lines ensures both support and resistance are well-defined
- Quality is foundational; poor quality patterns are unreliable regardless of other factors

#### Component 2: Compression Score (Weight: 30%)

**Definition**: Measures how tight the triangle has become (proximity to apex).

**Calculation:**
- **Formula**: `compression_score = 1 - compression`
- Where `compression = distance_end / distance_start` (from pattern detection)
- **Normalization**: Clamped to [0, 1] range

**Rationale**:
- Lower compression (narrower triangle) indicates more energy built up
- Stocks near the apex have higher potential for explosive moves
- This is the highest-weighted component, reflecting the importance of pattern maturity

**Example**:
- Compression = 0.3 (triangle narrowed to 30% of original width) → Score = 0.7
- Compression = 0.7 (triangle narrowed to 70% of original width) → Score = 0.3

#### Component 3: Volume Score (Weight: 30%)

**Definition**: Measures whether breakout is accompanied by increased trading volume.

**Calculation:**
1. **Recent Volume**: Most recent day's volume
2. **Average Volume**: Rolling 20-day average of volume
3. **Relative Volume**: `rel_vol = recent_volume / avg_volume`
4. **Normalization**: `volume_score = min(1, rel_vol / 2.0)`
   - If relative volume = 2.0× average, score = 1.0
   - If relative volume = 1.0× average, score = 0.5
   - If relative volume < 1.0× average, score < 0.5

**Rationale**:
- Breakouts without volume are often false signals
- Volume confirms institutional or significant retail participation
- 2× average volume is considered "full confirmation" threshold

#### Component 4: Breakout Strength Score (Weight: 10%)

**Definition**: Measures how decisively price has moved above the trendline.

**Calculation:**
- **Raw Strength**: `breakout_strength = (current_price / upper_trendline_value) - 1`
- **Normalization**: `strength_score = min(1, breakout_strength / 0.03)`
  - If strength = 3% above line, score = 1.0
  - If strength = 1.5% above line, score = 0.5
  - If strength < 0% (below line), score = 0

**Rationale**:
- Stronger breakouts (further above line) indicate more conviction
- 3% threshold represents a meaningful move above resistance
- Prevents weak breakouts from scoring highly

#### Component 5: Freshness Score (Weight: 10%)

**Definition**: Rewards recently detected breakouts over older ones.

**Calculation:**
- **Breakout Age = 1 day**: Score = 1.0 (full credit)
- **Breakout Age = 2 days**: Score = 0.7 (reduced credit)
- **Breakout Age > 2 days**: Score = 0.0 (disqualified at quality gate)

**Rationale**:
- First-day breakouts offer best entry opportunity
- Second-day breakouts may still be early but less optimal
- Older breakouts excluded to focus on fresh opportunities

#### Component 6: Volatility Bonus (Additive, Scale: 10 points)

**Definition**: Additional points for stocks with healthy momentum/volatility.

**Calculation:**
1. **Daily Returns**: Calculate percentage change between consecutive closes
2. **Standard Deviation**: `σ_daily = std(daily_returns)`
3. **Annualized Volatility**: `σ_annual = σ_daily × √252`
   - **Rationale**: Scales daily volatility to annual using square root of trading days
4. **Normalization**: `vol_score = min(1, σ_annual / 0.50)`
   - If annual volatility = 50%, score = 1.0
   - If annual volatility = 25%, score = 0.5
5. **Bonus Points**: `volatility_bonus = vol_score × 10`

**Rationale**:
- Moderate volatility (20-50%) indicates active trading and potential for moves
- Very low volatility (<10%) may indicate lack of interest
- Very high volatility (>50%) may indicate excessive risk
- Bonus is additive, not weighted, to reward momentum without over-weighting

### Final Score Calculation

**Weighted Sum:**
```
base_score = (
    quality_score × 0.20 +
    compression_score × 0.30 +
    volume_score × 0.30 +
    strength_score × 0.10 +
    freshness_score × 0.10
)
```

**Scaling and Bonus:**
```
final_score = (base_score × 100) + (volatility_bonus × 10)
```

**Capping:**
- Final score clamped to maximum of 100
- Minimum score is 0 (if any disqualifying condition met)

**Output**: Score between 0 and 100 for each candidate

---

## Stage 5: Ranking and Selection

### Purpose
Sort candidates by score and select top performers.

### Process

1. **Sorting**: All candidates sorted by final score in descending order (highest first)

2. **Top N Selection**: Select top 10 candidates (configurable via `top_n` parameter)

3. **Output**: Generate charts and analysis for selected tickers

### Rationale for Top 10

- **Diversification**: 10 stocks provide reasonable portfolio diversification
- **Quality Focus**: Top 10 represent the strongest signals, reducing false positives
- **Manageability**: 10 charts are manageable for manual review and analysis
- **Performance**: Balances thoroughness with computational efficiency

---

## Complete Pipeline Summary

```
Input: ~1000-2000 tickers (S&P 500 + NASDAQ + Dow)

    ↓
[Stage 1: Coarse Filtering]
    - Market Cap ≥ $2B
    - Data Sufficiency (≥170 days)
    - Price > SMA_150
    - SMA Slope ≥ 0
    ↓
~200-400 candidates

    ↓
[Stage 2: Pattern Detection]
    - For each candidate:
      * Test 33 time windows (40-360 days)
      * Find extrema points
      * Fit trendlines (weighted regression)
      * Check convergence
      * Detect breakouts
      * Select best window
    ↓
~20-50 candidates with valid patterns

    ↓
[Stage 3: Quality Gate]
    - is_converging = True
    - is_breaking_out = True
    - r2_high ≥ 0.5
    ↓
~10-30 candidates

    ↓
[Stage 4: Scoring]
    - Calculate 5-component weighted score
    - Add volatility bonus
    - Score range: 0-100
    ↓
~10-30 scored candidates

    ↓
[Stage 5: Ranking]
    - Sort by score (descending)
    - Select top 10
    ↓
Top 10 tickers for chart generation
```

---

## Key Algorithmic Choices and Rationale

### 1. Why Adaptive Windows?

**Problem**: Different stocks form triangles over different timeframes.

**Solution**: Test multiple windows and select the one with highest R².

**Benefit**: Captures patterns regardless of formation period, maximizing detection rate.

### 2. Why Weighted Regression for Upper Trendline?

**Problem**: Old extrema may not reflect current market conditions.

**Solution**: Weight recent extrema 5× more than old extrema.

**Benefit**: Trendline reflects current resistance level more accurately.

### 3. Why 1-2 Day Breakout Window?

**Problem**: Too early (same day) may be false signal; too late (>2 days) may have already moved.

**Solution**: Require exactly 1-2 days above trendline.

**Benefit**: Captures fresh breakouts at optimal entry timing.

### 4. Why Compression is Highest Weighted (30%)?

**Rationale**: Compression indicates pattern maturity and energy buildup. A stock at the apex of a tight triangle has maximum potential for explosive moves. This is the most predictive factor for breakout magnitude.

### 5. Why Volume is Equally Weighted (30%)?

**Rationale**: Volume confirms the validity of the breakout. Without volume, breakouts often fail. This component ensures only breakouts with institutional or significant retail participation are selected.

### 6. Why R² Threshold of 0.5?

**Rationale**: R² < 0.5 indicates poor linear fit. In statistical terms, the trendline explains less than 50% of the variance in extrema points, making the pattern unreliable. This threshold ensures only statistically significant patterns proceed.

### 7. Why Volatility Bonus is Additive?

**Rationale**: Volatility indicates momentum and trading interest, but shouldn't dominate the score. Making it additive (rather than weighted) allows it to boost scores of otherwise strong candidates without allowing high-volatility, low-quality patterns to score highly.

---

## Mathematical Foundations

### Linear Regression (Trendline Fitting)

**Model**: `y = β₀ + β₁x + ε`

Where:
- `y` = price (High or Low)
- `x` = time index
- `β₀` = intercept
- `β₁` = slope
- `ε` = error term

**Weighted Least Squares Solution**:
- Minimizes: `Σ wᵢ(yᵢ - β₀ - β₁xᵢ)²`
- Where `wᵢ` = weight for point `i`

### R² (Coefficient of Determination)

**Formula**: `R² = 1 - (SS_res / SS_tot)`

Where:
- `SS_res` = Σ(yᵢ - ŷᵢ)² (sum of squared residuals)
- `SS_tot` = Σ(yᵢ - ȳ)² (total sum of squares)
- `ŷᵢ` = predicted value from regression
- `ȳ` = mean of observed values

**Interpretation**:
- R² = 1.0: Perfect fit (all points on line)
- R² = 0.8: Line explains 80% of variance
- R² = 0.5: Line explains 50% of variance (minimum threshold)
- R² = 0.0: Line explains no variance (no relationship)

### Annualized Volatility

**Formula**: `σ_annual = σ_daily × √N`

Where:
- `σ_daily` = standard deviation of daily returns
- `N` = number of trading days per year (typically 252)

**Rationale**: Volatility scales with square root of time due to independence of daily returns (assuming random walk).

---

## Performance Optimizations

### Parallel Processing

- Pattern detection runs in parallel across multiple CPU cores
- Each ticker analyzed independently in separate process
- Typical configuration: 10 parallel workers
- **Benefit**: Reduces total scan time from hours to minutes

### Caching Strategy

- Historical price data cached to disk (Parquet format)
- Cache expires after 12 hours
- **Benefit**: Avoids redundant API calls, speeds up repeated scans

### Early Termination

- Quality gate eliminates candidates before expensive scoring
- Breakdown detection immediately disqualifies stocks
- **Benefit**: Reduces computational load on unpromising candidates

---

## Conclusion

The selection logic combines fundamental screening, statistical pattern recognition, and multi-factor scoring to identify the most promising breakout candidates. By systematically filtering thousands of stocks through increasingly sophisticated criteria, the system surfaces the top 10 tickers that exhibit:

1. **Strong fundamentals** (market cap, trend direction)
2. **Clean technical patterns** (high R² convergence triangles)
3. **Fresh breakouts** (1-2 days above resistance)
4. **Volume confirmation** (institutional participation)
5. **Pattern maturity** (high compression, near apex)
6. **Momentum** (volatility bonus)

This multi-stage approach balances thoroughness with efficiency, ensuring only the highest-quality opportunities are selected for further analysis and chart generation.
