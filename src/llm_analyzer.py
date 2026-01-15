import os
import re
import logging
from dotenv import load_dotenv
from openai import OpenAI
from typing import Dict

load_dotenv()
logger = logging.getLogger(__name__)


class LLMAnalyzer:
    def __init__(self, config: Dict):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = config.get('model', "gpt-4o")
        self.temperature = config.get('temperature', 0)
        self.reasoning_effort = config.get('reasoning_effort', "medium")
        self.system_role = config.get('system_role', "You are a senior equity research analyst.")
        self.prompt_template = config.get('prompt_template', "")

    def get_equity_report(self, ticker: str) -> Dict[str, str]:
        """
        Creates a full analysis report based on the professional prompt you defined.
        """
        if not self.prompt_template:
            return {"report": "Error: No prompt template found in config.", "sentiment": "ERROR"}

        prompt = self.prompt_template.format(ticker=ticker)

        # Detect if we're using a new generation model (GPT-5 and above)
        is_new_gen = self.model.startswith("gpt-5") or "o1" in self.model
        role = "developer" if is_new_gen else "system"
        messages = [
            {"role": role, "content": self.system_role},
            {"role": "user", "content": prompt}
        ]
        api_params = {
            "model": self.model,
            "messages": messages
        }

        if is_new_gen:
            # New generation models use reasoning effort instead of temperature
            api_params["reasoning_effort"] = self.reasoning_effort
        else:
            # Older models require temperature
            api_params["temperature"] = self.temperature
        
        try:
            response = self.client.chat.completions.create(**api_params)
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