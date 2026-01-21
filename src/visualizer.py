import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Visualizer:
    def __init__(self, config: dict):
        self.charts_output_dir = config.get('charts_output_dir', 'reports/charts')
        self.sma_period = config.get('sma_period', 150)
        self.show_plot = config.get('show_plot', False)
        # Create the output directory if it doesn't exist
        if not os.path.exists(self.charts_output_dir):
            os.makedirs(self.charts_output_dir)

    def create_chart(self, ticker: str, df: pd.DataFrame, pattern: dict, score: float):
        """
        Creates an interactive chart with candlestick, trend lines, and volume, and saves it as an HTML file.
        """
        logger.info(f"Generating chart for {ticker}...")
        
        # 1. Creating subplots with secondary y-axis for volume
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
            subplot_titles=('Price', 'Volume')
        )
        
        # 2. Adding the candlestick chart to the first subplot
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name=f'{ticker} Price'
            ),
            row=1, col=1
        )

        # 3. Adding a 150-day moving average (SMA)
        # We calculate it here to ensure it is always updated based on the received DataFrame
        sma_150 = df['Close'].rolling(window=self.sma_period).mean()

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=sma_150,
                mode='lines',
                name=f'SMA {self.sma_period}',
                line=dict(color='rgba(100, 149, 237, 0.9)', width=1.5) # Blue-ish color
            ),
            row=1, col=1
        )

        # 4. Adding trend lines (if they exist in the detection results)
        # We use different colors for the upper (resistance) and lower (support) lines
        if 'trendlines' in pattern:
            upper = pattern['trendlines']['upper']
            lower = pattern['trendlines']['lower']

            # Resistance line (red)
            if upper is not None:
                fig.add_trace(
                    go.Scatter(
                        x=upper.index,
                        y=upper.values,
                        mode='lines',
                        name='Resistance (Upper)',
                        line=dict(color='rgba(255, 50, 50, 0.8)', width=2, dash='dash')
                    ),
                    row=1, col=1
                )

            # Support line (green)
            if lower is not None:
                fig.add_trace(
                    go.Scatter(
                        x=lower.index,
                        y=lower.values,
                        mode='lines',
                        name='Support (Lower)',
                        line=dict(color='rgba(50, 255, 50, 0.8)', width=2, dash='dash')
                    ),
                    row=1, col=1
                )
            
        # 5. Adding volume bars to the second subplot (if Volume column exists)
        # Color volume bars: green for up days, red for down days
        if 'Volume' in df.columns:
            colors = ['rgba(50, 255, 50, 0.6)' if close >= open else 'rgba(255, 50, 50, 0.6)' 
                      for close, open in zip(df['Close'], df['Open'])]
            
            fig.add_trace(
                go.Bar(
                    x=df.index,
                    y=df['Volume'],
                    name='Volume',
                    marker_color=colors,
                    showlegend=False
                ),
                row=2, col=1
            )
        else:
            logger.warning(f"Volume column not found for {ticker}, skipping volume chart")

        # 6. Adding an indication of the breakout (if it happened)
        if pattern.get('is_breaking_down', False):
            fig.add_annotation(
                x=df.index[-1], y=df['Low'].iloc[-1],
                text="⚠️ BEARISH BREAKDOWN",
                showarrow=True, arrowhead=1, arrowcolor="red",
                bgcolor="white", font=dict(color="red"),
                row=1, col=1
            )

        if pattern.get('is_breaking_out', False):
             fig.add_annotation(
                 x=df.index[-1], y=df['High'].iloc[-1],
                 text="🚀 BULLISH BREAKOUT",
                 showarrow=True, arrowhead=1, arrowcolor="gold",
                 bgcolor="black", font=dict(color="gold"),
                 row=1, col=1
             )

        # 7. Designing the title and general layout
        today_str = datetime.now().strftime('%Y-%m-%d')
        # Building the title with all the important information
        title_text = (
            f"<b>{ticker}</b> Analysis Report | Date: {today_str}<br>"
            f"Final Score: <b>{score:.2f}/100</b> | "
            f"Compression: {pattern.get('compression', 0):.2f} | "
            f"R² High: {pattern.get('r2_high', 0):.2f}"
        )

        fig.update_layout(
            title=title_text,
            template='plotly_dark',  # Dark theme that suits trading
            height=800,
            hovermode="x unified",  # Simplifies data reading
            showlegend=True
        )
        
        # Update y-axes labels
        fig.update_yaxes(title_text="Price (USD)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        fig.update_xaxes(title_text="Date", row=2, col=1)
        
        # Remove the range slider
        fig.update_layout(xaxis_rangeslider_visible=False)

        # 8. Saving to an HTML file
        filename = f"{ticker}_{today_str}_score_{int(score)}.html"
        file_path = os.path.join(self.charts_output_dir, filename)
        fig.write_html(file_path)
        
        logger.info(f"Chart saved successfully to: {file_path}")

        # Optional: opening the chart in the browser immediately
        if self.show_plot:
            fig.show()