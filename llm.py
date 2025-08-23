# llm.py
import requests
from datetime import datetime, timedelta
import re
from difflib import SequenceMatcher, get_close_matches
from properties import PropertiesController

# Load properties database
pc = PropertiesController()
properties = pc.load_properties()

# Extract all unique vocab from database
ALL_LOCATIONS = sorted(set(p.location for p in properties))
ALL_ENVIRONMENTS = sorted(set(p.environment for p in properties))
ALL_TYPES = sorted(set(p.type for p in properties))
ALL_FEATURES = sorted(set(f for p in properties for f in p.features))
ALL_TAGS = sorted(set(t for p in properties for t in p.tags))

# API endpoint
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = (
    "You are an assistant for an Airbnb-like vacation property search. "
    "Parse a USER REQUEST into Python dict fields: "
    "- location (str, city or region), "
    "- environment (str, e.g., mountains, beach, urban), "
    "- type (str, e.g., Chalet, Condo), "
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


# ---------- Date Handling ----------
def parse_date_safe(input_str: str, default_year=2025):
    if not input_str or not isinstance(input_str, str):
        return None
    for fmt in ("%Y-%m-%d", "%b %d %Y", "%B %d %Y", "%b %d", "%B %d"):
        try:
            input_full = input_str if "%Y" in fmt else f"{input_str} {default_year}"
            return datetime.strptime(input_full, fmt).date()
        except ValueError:
            continue
    return None

def expand_dates(start: str, end: str):
    start_dt = parse_date_safe(start)
    end_dt = parse_date_safe(end)
    if not start_dt or not end_dt or end_dt < start_dt:
        return []
    return [(start_dt + timedelta(days=i)).isoformat() for i in range((end_dt - start_dt).days + 1)]


# ---------- LLM Helpers ----------
def llm_call(prompt, role="user", model=MODEL, api_key=None, sys_prompt=None):
    if not api_key:
        return None
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    messages = []
    if sys_prompt:
        messages.append({"role": "system", "content": sys_prompt})
    messages.append({"role": role, "content": prompt})
    payload = {"model": model, "messages": messages, "temperature": 0.0}
    r = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
    if r.status_code != 200:
        return None
    data = r.json()
    return (data.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()


# ---------- Normalization ----------
def llm_normalize_term(user_term, valid_list, field_name, api_key=None):
    """Normalize a term to closest DB option, auto-accept if obvious synonym."""
    prompt = (
        f"The user asked for '{user_term}' as a {field_name}. "
        f"Valid options are: {valid_list}. "
        f"Which one best matches '{user_term}'? "
        f"Return ONLY one option. If it's an obvious synonym, just return it."
    )
    content = llm_call(prompt, api_key=api_key, sys_prompt=f"You are a synonym resolver for {field_name}.")
    if content and content in valid_list:
        ratio = SequenceMatcher(None, user_term.lower(), content.lower()).ratio()
        auto_accept = ratio > 0.65
        return content, auto_accept
    return None, False

def normalize_features_and_tags(parsed, api_key):
    def process_list(user_list, valid_list, field_name):
        result = []
        for item in user_list:
            if item in valid_list:
                result.append(item)
            else:
                alt, auto = llm_normalize_term(item, valid_list, field_name, api_key=api_key)
                if alt:
                    if auto:
                        result.append(alt)
                    else:
                        ans = input(f"Bot: I didn’t find '{item}', but I matched it to '{alt}'. Use that? (yes/no): ").strip().lower()
                        if ans in ["yes", "y", "ok", "sure"]:
                            result.append(alt)
        return result
    parsed["features"] = process_list(parsed.get("features", []), ALL_FEATURES, "feature")
    parsed["tags"] = process_list(parsed.get("tags", []), ALL_TAGS, "tag")
    return parsed

def normalize_env_and_type(parsed, api_key):
    if parsed.get("environment") and parsed["environment"] not in ALL_ENVIRONMENTS:
        alt, auto = llm_normalize_term(parsed["environment"], ALL_ENVIRONMENTS, "environment", api_key=api_key)
        if alt:
            parsed["environment"] = alt if auto else (
                alt if input(f"Bot: Change '{parsed['environment']}' to '{alt}'? (yes/no): ").strip().lower() in ["yes","y"] else parsed["environment"]
            )
    if parsed.get("type") and parsed["type"] not in ALL_TYPES:
        alt, auto = llm_normalize_term(parsed["type"], ALL_TYPES, "property type", api_key=api_key)
        if alt:
            parsed["type"] = alt if auto else (
                alt if input(f"Bot: Change '{parsed['type']}' to '{alt}'? (yes/no): ").strip().lower() in ["yes","y"] else parsed["type"]
            )
    return parsed


# ---------- Location Handling ----------
def llm_geography_map(user_location, all_locations, api_key=None, multi=False):
    if multi:
        prompt = (
            f"The user entered '{user_location}', which may be a region. "
            f"From this list of valid locations: {all_locations}, "
            f"return one or more matching locations (comma-separated)."
        )
    else:
        prompt = (
            f"The user entered '{user_location}', but it is not in the database. "
            f"Valid locations are: {all_locations}. "
            f"Which is geographically closest or most appropriate? Return ONLY one."
        )
    content = llm_call(prompt, api_key=api_key, sys_prompt="You are a geography expert.")
    if not content:
        return None
    if multi:
        return [loc.strip() for loc in content.split(",") if loc.strip() in all_locations]
    return content if content in all_locations else None

def map_location_to_db(location, all_locations, api_key=None):
    if not location:
        return None
    match = get_close_matches(location, all_locations, n=1, cutoff=0.75)
    if match:
        if match[0].lower() != location.lower():
            ans = input(f"Bot: I didn’t find '{location}', but I have '{match[0]}'. Use that? (yes/no): ").strip().lower()
            return match[0] if ans in ["yes", "y", "ok", "sure"] else None
        return match[0]
    geo_match = llm_geography_map(location, all_locations, api_key=api_key, multi=False)
    if geo_match:
        ans = input(f"Bot: I didn’t find '{location}', but I have '{geo_match}' nearby. Use that? (yes/no): ").strip().lower()
        return geo_match if ans in ["yes", "y", "ok", "sure"] else None
    geo_matches = llm_geography_map(location, all_locations, api_key=api_key, multi=True)
    if geo_matches:
        print(f"Bot: I didn’t find '{location}', but it may refer to {geo_matches}.")
        choice = input("Bot: Enter one of these options, or press Enter to skip: ").strip()
        return choice if choice in geo_matches else None
    return None


# ---------- Validation ----------
def validate_and_reprompt(parsed):
    max_capacity = max(p["capacity"] for p in properties)
    all_prices = [p["price"] for p in properties]
    min_price, max_price = min(all_prices), max(all_prices)

    if parsed.get("group_size") and parsed["group_size"] > max_capacity:
        print(f"Bot: Group size {parsed['group_size']} exceeds max capacity {max_capacity}.")
        ans = input(f"Bot: Adjust to {max_capacity}? (yes/no): ").strip().lower()
        if ans in ["yes","y"]: parsed["group_size"] = max_capacity
        else: parsed["error"] = "Group size too large."; return parsed

    budget = parsed.get("budget") or parsed.get("price_max")
    if budget and (budget < min_price or budget > max_price):
        print(f"Bot: Budget {budget} outside range {min_price}-{max_price}.")
        ans = input(f"Bot: Adjust to {max_price}? (yes/no): ").strip().lower()
        if ans in ["yes","y"]: parsed["budget"] = parsed["price_max"] = max_price
        else: parsed["error"] = "Budget out of range."; return parsed

    if parsed.get("location") and parsed.get("environment"):
        loc_envs = {p["environment"] for p in properties if p["location"] == parsed["location"]}
        if loc_envs and parsed["environment"] not in loc_envs:
            print(f"Bot: No '{parsed['environment']}' properties in {parsed['location']}.")
            ans = input(f"Bot: Change environment to {list(loc_envs)[0]}? (yes/no): ").strip().lower()
            if ans in ["yes","y"]: parsed["environment"] = list(loc_envs)[0]
            else: parsed["error"] = "Contradictory location/environment."; return parsed
    return parsed


# ---------- Main LLM Parser ----------
def llm_parse(model=MODEL, temperature=0.7):
    api_key = input("Enter API key: ").strip()
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    user_prompt = input("Bot: What kind of property are you looking for? ").strip()
    if not user_prompt: return {"error": "No input provided"}

    payload = {"model": model, "messages": [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}], "temperature": temperature}
    r = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
    if r.status_code != 200: return {"error": f"HTTP {r.status_code}", "details": r.text}
    data = r.json()
    content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
    try: parsed = eval(content) if content else {}
    except: parsed = {}

    if not parsed.get("location") and not parsed.get("environment"):
        choice = input("Bot: Please specify a location or environment: ").strip()
        parsed["location"] = choice

    if parsed.get("location"):
        mapped = map_location_to_db(parsed["location"], ALL_LOCATIONS, api_key=api_key)
        if mapped: parsed["location"] = mapped

    if not parsed.get("group_size"):
        try: parsed["group_size"] = int(input("Bot: How many people? ").strip())
        except: parsed["group_size"] = 1

    if parsed.get("budget") is None and parsed.get("price_max") is None:
        budget_input = input("Bot: What is your budget? (e.g. 1000 or 100-2500): ").strip()
        if "-" in budget_input:
            try:
                low, high = map(int, budget_input.split("-"))
                parsed["price_min"], parsed["price_max"], parsed["budget"] = low, high, high
            except: pass
        else:
            try:
                value = int(re.sub("[^0-9]", "", budget_input))
                parsed["price_min"], parsed["price_max"], parsed["budget"] = 0, value, value
            except: pass

    start = parsed.get("start_date") or input("Bot: Start date? (YYYY-MM-DD or Aug 20) ").strip()
    end = parsed.get("end_date") or input("Bot: End date? (YYYY-MM-DD or Aug 23) ").strip()
    start_dt, end_dt = parse_date_safe(start), parse_date_safe(end)
    if not start_dt or not end_dt:
        print("Bot: Could not parse dates, defaulting to tomorrow+1 day.")
        start_dt, end_dt = datetime.today().date(), datetime.today().date() + timedelta(days=1)
    parsed["start_date"], parsed["end_date"] = start_dt.isoformat(), end_dt.isoformat()
    parsed["dates"] = expand_dates(parsed["start_date"], parsed["end_date"])

    parsed = normalize_features_and_tags(parsed, api_key)
    parsed = normalize_env_and_type(parsed, api_key)
    parsed = validate_and_reprompt(parsed)

    print("Bot: Final request dictionary:")
    print(parsed)
    return parsed

# OpenAI. (2025). ChatGPT (GPT-5) [Large language model]. https://chat.openai.com