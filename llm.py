# llm.py
import requests
from datetime import datetime, timedelta
import re

# API endpoint for OpenRouter (or OpenAI if you switch URLs)
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
# OPENROUTER_URL = "https://api.openai.com/v1/chat/completions"
MODEL = "gpt-4o-mini"

# System prompt: tells the LLM how to format its output
# The assistant should return only a Python dictionary with these fields:
#   - location, environment, group_size, budget, price_min, price_max, features, tags, start_date, end_date
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

def parse_date_safe(input_str: str, default_year=2025):
    if not input_str or not isinstance(input_str, str):
        return None
    for fmt in ("%Y-%m-%d", "%b %d %Y", "%B %d %Y"):
        try:
            if "%Y" not in fmt:
                input_full = f"{input_str} {default_year}"
            else:
                input_full = input_str
            return datetime.strptime(input_full, fmt).date()
        except ValueError:
            continue
    return None

def expand_dates(start: str, end: str):
    """
    Generate a list of ISO-format dates between start and end (inclusive).
    Returns [] if dates are invalid or end < start.
    """
    start_dt = parse_date_safe(start)
    end_dt = parse_date_safe(end)
    if not start_dt or not end_dt or end_dt < start_dt:
        return []
    return [(start_dt + timedelta(days=i)).isoformat() for i in range((end_dt - start_dt).days + 1)]

def llm_parse(model=MODEL, temperature=0.7):
    """
    Interact with the user and the LLM to parse a vacation property request
    into a structured Python dictionary with required fields.
    """
    api_key = input("Enter API key: ").strip()
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    user_prompt = input("Bot: What kind of property are you looking for? ").strip()
    if not user_prompt:
        return {"error": "No input provided"}

    # Construct request payload for OpenRouter/OpenAI API
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

    # Extract content from API response
    data = r.json()
    content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")

    # Safely evaluate LLM output
    parsed = {}
    try:
        parsed = eval(content) if content else {}
        if not isinstance(parsed, dict):
            parsed = {}
    except:
        parsed = {}

    # Prompt for required fields if missing
    if not parsed.get("location"):
        parsed["location"] = input("Bot: What location are you interested in? ").strip()
    if not parsed.get("environment"):
        parsed["environment"] = input("Bot: What type of environment do you prefer (e.g., beach, urban, forest)? ").strip()
    if not parsed.get("group_size"):
        try:
            parsed["group_size"] = int(input("Bot: How many people will be traveling? ").strip())
        except ValueError:
            parsed["group_size"] = 1

    # Budget handling: ask if missing
    if parsed.get("budget") is None and parsed.get("price_min") is None and parsed.get("price_max") is None:
        budget_input = input("Bot: What is your budget? (You can enter a single number or a range like '100-250'): ").strip()
        if "-" in budget_input:
            try:
                low, high = map(int, budget_input.split("-"))
                parsed["price_min"] = low
                parsed["price_max"] = high
                parsed["budget"] = high
            except:
                value = int(re.sub("[^0-9]", "", budget_input)) if budget_input.isdigit() else 0
                parsed["price_min"] = 0
                parsed["price_max"] = value
                parsed["budget"] = value
        else:
            try:
                value = int(re.sub("[^0-9]", "", budget_input))
                parsed["price_max"] = value
                parsed["price_min"] = 0
                parsed["budget"] = value
            except:
                parsed["price_max"] = 0
                parsed["price_min"] = 0
                parsed["budget"] = 0

    parsed["price_min"] = parsed.get("price_min", 0)
    parsed["price_max"] = parsed.get("price_max", parsed.get("budget", 0))
    parsed["budget"] = parsed.get("budget", parsed.get("price_max", 0))

    # Parse or prompt for dates
    start = parsed.get("start_date") or input("Bot: What is your start date? (YYYY-MM-DD or 'Aug 20') ").strip()
    end = parsed.get("end_date") or input("Bot: What is your end date? (YYYY-MM-DD or 'Aug 23') ").strip()

    start_dt = parse_date_safe(start)
    end_dt = parse_date_safe(end)

    if not start_dt or not end_dt:
        print("Error: Could not parse dates, using defaults.")
        start_dt = datetime.today().date()
        end_dt = start_dt + timedelta(days=1)

    parsed["start_date"] = start_dt.isoformat()
    parsed["end_date"] = end_dt.isoformat()
    parsed["dates"] = expand_dates(parsed["start_date"], parsed["end_date"])

    # Optional fields
    parsed["features"] = parsed.get("features") or []
    parsed["tags"] = parsed.get("tags") or []

    print("Bot: LLM returned the following dictionary:")
    print(parsed)
    return parsed
