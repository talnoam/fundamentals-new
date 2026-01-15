import os
import re
from dotenv import load_dotenv
from openai import OpenAI
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class LLMAnalyzer:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o" # Faster execution with gpt-4o

    def get_equity_report(self, ticker: str) -> str:
        """
        Creates a full analysis report based on the professional prompt you defined.
        """
        prompt = f"""
        Act as an elite equity research analyst at a top-tier investment firm or hedge fund. 
        You were top in your class and your analysis is always top notch. 
        Analyze the following company using both fundamental and macroeconomic perspectives.

        Stock Ticker: {ticker}
        Investment Thesis: Breakout from technical consolidation (Triangle/Wedge pattern) identified by quantitative scanner.
        Goal: Provide a comprehensive long/short thesis validation.

        Use the following structure to deliver a clear, well-reasoned equity research report:
        1. Fundamental Analysis
        2. Analyze revenue growth, gross & net margin trends, free cash flow
        3. Compare valuation metrics vs sector peers (P/E, EV/EBITDA, etc.)
        4. Review insider ownership and recent insider trades
        5. Thesis Validation
        6. Present 3 arguments supporting the thesis
        7. Highlight 2 counter-arguments or key risks
        8. Provide a final verdict: Bullish / Bearish / Neutral with justification
        9. Sector & Macro View
        10. Give a short sector overview
        11. Outline relevant macroeconomic trends
        12. Explain company’s competitive positioning
        13. Catalyst Watch
        14. List upcoming events (earnings, product launches, regulation, etc.)
        15. Identify both short-term and long-term catalysts
        16. Investment Summary
        17. 5-bullet investment thesis summary
        18. Final recommendation: Buy / Hold / Sell
        19. Confidence level (High / Medium / Low)
        20. Expected timeframe (e.g. 6–12 months)

        Build the report this way:
        Use markdown
        Use bullet points where appropriate
        Be concise, professional, and insight-driven
        Do not explain your process just deliver the analysis

        IMPORTANT: At the very end of your response, add a single line in this format:
        FINAL_SENTIMENT: [BULLISH/BEARISH/NEUTRAL]
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a senior equity research analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            full_content = response.choices[0].message.content
            
            # Extract the sentiment using Regex
            sentiment_match = re.search(r"FINAL_SENTIMENT:\s*(BULLISH|BEARISH|NEUTRAL)", full_content, re.IGNORECASE)
            sentiment = sentiment_match.group(1).upper() if sentiment_match else "NEUTRAL"
            
            # Clean the sentiment tag from the displayed report to the user
            clean_report = re.sub(r"FINAL_SENTIMENT:.*", "", full_content).strip()
            
            return {
                "report": clean_report,
                "sentiment": sentiment
            }
        except Exception as e:
            logger.error(f"LLM Analysis failed for {ticker}: {e}")
            return {"report": f"Error: {e}", "sentiment": "ERROR"}