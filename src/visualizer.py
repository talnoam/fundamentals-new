import plotly.graph_objects as go
import pandas as pd
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Visualizer:
    def __init__(self, config: dict):
        self.output_dir = config.get('output_dir', 'reports/charts')
        # Create the output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def create_chart(self, ticker: str, df: pd.DataFrame, pattern: dict, score: float, show_plot: bool = True):
        """
        Creates an interactive chart with candlestick and trend lines, and saves it as an HTML file.
        """
        logger.info(f"Generating chart for {ticker}...")
        
        # 1. Creating the base chart (candlestick)
        fig = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name=f'{ticker} Price'
        )])

        # 2. Adding trend lines (if they exist in the detection results)
        # We use different colors for the upper (resistance) and lower (support) lines
        if 'trendlines' in pattern:
            # Resistance line (red)
            fig.add_trace(go.Scatter(
                x=df.index,
                y=pattern['trendlines']['upper'],
                mode='lines',
                name='Resistance (Upper)',
                line=dict(color='rgba(255, 50, 50, 0.8)', width=2, dash='dash')
            ))

            # Support line (green)
            fig.add_trace(go.Scatter(
                x=df.index,
                y=pattern['trendlines']['lower'],
                mode='lines',
                name='Support (Lower)',
                line=dict(color='rgba(50, 255, 50, 0.8)', width=2, dash='dash')
            ))
            
        # 3. Adding an indication of the breakout (if it happened)
        if pattern.get('is_breaking_out', False):
             # Adding an arrow or marking on the last candlestick
             last_date = df.index[-1]
             last_high = df['High'].iloc[-1]
             fig.add_annotation(
                 x=last_date, y=last_high,
                 text="BREAKOUT!",
                 showarrow=True, arrowhead=1, arrowcolor="yellow",
                 bgcolor="black", opacity=0.8
             )

        # 4. Designing the title and general layout
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
            yaxis_title='Price (USD)',
            xaxis_title='Date',
            template='plotly_dark',  # Dark theme that suits trading
            xaxis_rangeslider_visible=False, # Hides the bottom slider for a cleaner look
            height=700,
            hovermode="x unified" # Simplifies data reading
        )

        # 5. Saving to an HTML file
        filename = f"{ticker}_{today_str}_score_{int(score)}.html"
        file_path = os.path.join(self.output_dir, filename)
        fig.write_html(file_path)
        
        logger.info(f"Chart saved successfully to: {file_path}")

        # Optional: opening the chart in the browser immediately
        if show_plot:
            fig.show()