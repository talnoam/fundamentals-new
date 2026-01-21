import os
import re
import logging
from dotenv import load_dotenv
from openai import OpenAI
from serpapi import GoogleSearch
from typing import Dict

load_dotenv()
logger = logging.getLogger(__name__)


class LLMAnalyzer:
    def __init__(self, config: Dict):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.serpapi_key = os.getenv("SERPAPI_KEY")
        self.model = config.get('model', "gpt-4o")
        self.temperature = config.get('temperature', 0)
        self.reasoning_effort = config.get('reasoning_effort', "medium")
        self.prompts = config.get('prompts', {})
        self.system_roles = config.get('system_roles', {})

    def _get_latest_news(self, ticker: str) -> str:
        """
        retrieves the latest news for the ticker to provide the analyst with 'Hard Data' up to date.
        """
        if not self.serpapi_key:
            logger.warning("No SERPAPI_KEY found, skipping news retrieval.")
            return "No recent news metadata available."

        try:
            # focused search for news and catalysts (like in USAR)
            search_query = f"{ticker} stock news catalyst press release"
            params = {
                "engine": "google",
                "q": search_query,
                "tbm": "nws", # search only in news
                "api_key": self.serpapi_key
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            news_items = []
            if "news_results" in results:
                # take the 5 latest headlines
                for item in results["news_results"][:5]:
                    title = item.get("title", "")
                    snippet = item.get("snippet", "")
                    date = item.get("date", "Recent")
                    news_items.append(f"[{date}] {title}: {snippet}")
            
            return "\n".join(news_items) if news_items else "No recent news found."
            
        except Exception as e:
            logger.error(f"Search failed for {ticker}: {e}")
            return "Error retrieving recent news."

    def get_equity_report(self, ticker: str, report_type: str = "fundamental") -> Dict[str, str]:
        """
        Creates a full analysis report based on the professional prompt you defined.
        """
        prompt_template = self.prompts.get(report_type, "")
        system_role = self.system_roles.get(report_type, "You are an analyst.")

        if not prompt_template:
            return {"report": "Error: Prompt not found.", "sentiment": "ERROR"}

        # --- upgrade: bring the news before sending to the LLM ---
        latest_news = self._get_latest_news(ticker)

        full_context_prompt = (
            f"{prompt_template.format(ticker=ticker)}\n\n"
            f"--- LATEST NEWS & CATALYSTS FOR {ticker} ---\n"
            f"{latest_news}\n"
            f"--- END OF NEWS ---"
        )

        # Detect if we're using a new generation model (GPT-5 and above)
        is_new_gen = self.model.startswith("gpt-5") or "o1" in self.model
        role = "developer" if is_new_gen else "system"
        messages = [
            {"role": role, "content": system_role},
            {"role": "user", "content": full_context_prompt}
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