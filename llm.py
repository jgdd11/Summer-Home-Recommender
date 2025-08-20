# llm.py
import requests
from datetime import datetime, timedelta
import re

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = (
    "You are an assistant for an Airbnb-like vacation property search. "
    "Parse a USER REQUEST into Python dict fields: "
    "- location (str, city or region), "
    "- environment (str, e.g., mountains, beach, urban), "
    "- group_size (int, number of guests), "
    "- budget (int, optional), "
    "- price_min (int, optional), "
    "- price_max (int, optional), "
    "- features (list[str], optional), "
    "- tags (list[str], optional), "
    "- start_date (str, YYYY-MM-DD, optional), "
    "- end_date (str, YYYY-MM-DD, optional). "
    "Return ONLY a Python dictionary, not a JSON string."
)

def parse_date(input_str: str):
    """Converts a string like 'Aug 20' or 'YYYY-MM-DD' to a datetime object, defaulting year 2025."""
    for fmt in ("%Y-%m-%d", "%b %d %Y", "%B %d %Y"):
        try:
            if "%Y" not in fmt:
                input_str_full = f"{input_str} 2025"
            else:
                input_str_full = input_str
            return datetime.strptime(input_str_full, fmt)
        except ValueError:
            continue
    return None

def expand_dates(start: str, end: str):
    """Returns list of date strings YYYY-MM-DD from start to end."""
    start_dt = parse_date(start)
    end_dt = parse_date(end)
    if not start_dt or not end_dt or end_dt < start_dt:
        raise ValueError("Invalid start or end date.")
    return [(start_dt + timedelta(days=i)).strftime("%Y-%m-%d") for i in range((end_dt - start_dt).days + 1)]

def llm_parse(model=MODEL, temperature=0.7):
    api_key = input("Enter API key: ").strip()
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
    content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")

    # Parse LLM output safely
    parsed = {}
    try:
        parsed = eval(content) if content else {}
        if not isinstance(parsed, dict):
            parsed = {}
    except:
        parsed = {}

    # Prompt user for missing required fields
    if not parsed.get("location"):
        parsed["location"] = input("Bot: What location are you interested in? ").strip()

    if not parsed.get("environment"):
        parsed["environment"] = input("Bot: What type of environment do you prefer (e.g., beach, urban, forest)? ").strip()

    if not parsed.get("group_size"):
        try:
            parsed["group_size"] = int(input("Bot: How many people will be traveling? ").strip())
        except ValueError:
            parsed["group_size"] = 1

    # Dates
    if not parsed.get("start_date") or not parsed.get("end_date"):
        start = input("Bot: What is your start date? (YYYY-MM-DD or 'Aug 20') ").strip()
        end = input("Bot: What is your end date? (YYYY-MM-DD or 'Aug 23') ").strip()
        parsed["start_date"] = parse_date(start).strftime("%Y-%m-%d")
        parsed["end_date"] = parse_date(end).strftime("%Y-%m-%d")
    parsed["dates"] = expand_dates(parsed["start_date"], parsed["end_date"])
    # Features and tags (optional)
    parsed["features"] = parsed.get("features") or []
    parsed["tags"] = parsed.get("tags") or []

    # Budget handling
    if parsed.get("budget") is not None:
        parsed["price_max"] = parsed["budget"]
        parsed["price_min"] = 0
    parsed["price_min"] = parsed.get("price_min", 0)
    parsed["price_max"] = parsed.get("price_max", parsed.get("budget", 0))

    print("Bot: LLM returned the following dictionary:")
    print(parsed)

    return parsed

