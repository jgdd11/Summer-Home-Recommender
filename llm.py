# llm.py
import requests
from datetime import datetime, timedelta
import getpass

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-chat"

SYSTEM_PROMPT = (
    "You are an assistant for an Airbnb-like vacation property search. "
    "Parse a USER REQUEST into Python dict fields: "
    "- location (str, city or region), "
    "- environment (str, e.g., mountains, beach, urban), "
    "- group_size (int, number of guests), "
    "- price_min (int, optional), "
    "- price_max (int, optional), "
    "- features (list[str], optional), "
    "- tags (list[str], optional), "
    "- start_date (str, YYYY-MM-DD, optional), "
    "- end_date (str, YYYY-MM-DD, optional). "
    "Return ONLY a Python dictionary, not a JSON string."
)


def llm_parse(api_key, model=MODEL, temperature=0.7):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    user_prompt = input("Bot: What kind of property are you looking for? ").strip()
    if not user_prompt:
        return {"error": "No input provided"}

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
    
    # Try parsing LLM output to a dict
    parsed = {}
    try:
        parsed = eval(content) if content else {}
        if not isinstance(parsed, dict):
            parsed = {}
    except:
        parsed = {}

    # Required fields
    required_fields = {
        "location": "Please provide the city or region for your stay: ",
        "environment": "What kind of environment do you prefer? (e.g., beach, mountains, urban): ",
        "group_size": "How many guests will be staying? "
    }
    
    for key, prompt_text in required_fields.items():
        while key not in parsed or not parsed.get(key):
            val = input(f"Bot: {prompt_text}").strip()
            if key == "group_size":
                try:
                    val = int(val)
                except ValueError:
                    print("Bot: Please enter a valid number for group size.")
                    continue
            parsed[key] = val

    # Booking dates
    if "start_date" not in parsed or "end_date" not in parsed:
        start = input("Bot: What is your start date? (YYYY-MM-DD): ").strip()
        end = input("Bot: What is your end date? (YYYY-MM-DD): ").strip()
        parsed["start_date"] = start
        parsed["end_date"] = end

    parsed["dates"] = expand_dates(parsed["start_date"], parsed["end_date"])
    
    return parsed  # <-- always a Python dict


def expand_dates(start: str, end: str):
    start_dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")
    days = (end_dt - start_dt).days
    return [(start_dt + timedelta(days=i)) for i in range(days+1)]  # datetime objects
