# llm.py
import requests
import json
from datetime import datetime, timedelta
import getpass

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-chat"   # can override from main.py

SYSTEM_PROMPT = (
    "You are a helpful assistant for an Airbnb-like vacation property search. "
    "Parse a USER REQUEST into structured JSON fields. "
    "Return ONLY JSON with these keys: "
    " - 'location' (str, optional) "
    " - 'price_max' (int, optional, budget ceiling in USD) "
    " - 'price_min' (int, optional) "
    " - 'features' (list[str], optional) "
    " - 'tags' (list[str], optional) "
    " - 'start_date' (str, YYYY-MM-DD, optional) "
    " - 'end_date' (str, YYYY-MM-DD, optional). "
    "Do NOT generate lists of dates yourself."
)


def llm_parse(model=MODEL, temperature=0.7):
    """
    Prompt the user for what they want, send it to the LLM, and return parsed JSON.
    """
    api_key = getpass.getpass("Enter your OpenRouter API key (input is hidden): ").strip()                    
    user_prompt = input("Bot: What kind of property are you looking for? ").strip()
    if not user_prompt:
        return {"error": "No input provided"}

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
    }

    r = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
    if r.status_code != 200:
        return {"error": f"HTTP {r.status_code}", "details": r.text}

    data = r.json()
    content = (data.get("choices") or [{}])[0].get("message", {}).get("content")
    if not content:
        return {"error": "Empty response", "raw": data}

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # fallback: extract substring
        s, e = content.find("{"), content.rfind("}")
        if s != -1 and e != -1 and e > s:
            try:
                return json.loads(content[s:e+1])
            except json.JSONDecodeError:
                return {"error": "Non-JSON content", "raw": content}
        return {"error": "Non-JSON content", "raw": content}


def expand_dates(start: str, end: str):
    """
    Expand a start and end date (YYYY-MM-DD) into a list of consecutive dates, inclusive.
    """
    start_dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")
    days = (end_dt - start_dt).days
    return [(start_dt + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days+1)]
