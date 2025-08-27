import requests
from datetime import datetime, timedelta
import re
from difflib import SequenceMatcher, get_close_matches
from properties import PropertiesController

# Load properties database
pc = PropertiesController()
properties = pc.load_properties()

# Extract unique vocab from database
ALL_LOCATIONS = sorted(set(p.location for p in properties))
ALL_ENVIRONMENTS = sorted(set(p.environment for p in properties))
ALL_TYPES = sorted(set(p.type for p in properties))
ALL_FEATURES = sorted(set(f for p in properties for f in p.features))
ALL_TAGS = sorted(set(t for p in properties for t in p.tags))

# API endpoint
API_ENDPOINT_URL = "https://openrouter.ai/api/v1/chat/completions" # OpenRouter
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
    r = requests.post(API_ENDPOINT_URL, headers=headers, json=payload, timeout=60)
    if r.status_code != 200:
        return None
    data = r.json()
    return (data.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()

# ---------- Synonym Normalization ----------
def normalize_with_llm(user_term, valid_list, field_name, api_key=None):
    """Ask LLM to map a user term to a valid DB entry (synonym resolution)."""
    if not user_term:
        return None
    if user_term in valid_list:
        return user_term
    prompt = (
        f"The user asked for '{user_term}' as a {field_name}. "
        f"Valid {field_name}s in the database are: {valid_list}. "
        "Which one is the closest synonym or best match? "
        "Return ONLY one option."
    )
    alt = llm_call(prompt, api_key=api_key, sys_prompt=f"You are a synonym resolver for {field_name}.")
    if alt and alt in valid_list:
        return alt
    return None

def normalize_features_and_tags(parsed, api_key):
    def process_list(user_list, valid_list, field_name):
        result = []
        for item in user_list:
            mapped = normalize_with_llm(item, valid_list, field_name, api_key=api_key)
            if mapped:
                result.append(mapped)
        return result

    parsed["features"] = process_list(parsed.get("features", []), ALL_FEATURES, "feature")
    parsed["tags"] = process_list(parsed.get("tags", []), ALL_TAGS, "tag")
    return parsed

def normalize_env_and_type(parsed, api_key):
    if parsed.get("environment") and parsed["environment"] not in ALL_ENVIRONMENTS:
        alt = normalize_with_llm(parsed["environment"], ALL_ENVIRONMENTS, "environment", api_key=api_key)
        if alt:
            parsed["environment"] = alt
    if parsed.get("type") and parsed["type"] not in ALL_TYPES:
        alt = normalize_with_llm(parsed["type"], ALL_TYPES, "property type", api_key=api_key)
        if alt:
            parsed["type"] = alt
    return parsed

# ---------- Location & Environment ----------
def map_location_to_db(location, all_locations, requested_env=None, api_key=None):
    """Map location + environment to DB, rerouting to the nearest valid option with LLM help."""

    # CASE 1: Location only
    if location and not requested_env:
        if location in all_locations:
            return location, None
        prompt = (
            f"The user asked for '{location}' as a vacation location. "
            f"My database contains these valid cities/regions: {all_locations}. "
            "Which one is the closest real-world match? Return ONLY the city/region name."
        )
        alt = llm_call(prompt, api_key=api_key, sys_prompt="You are a location resolver.")
        if alt and alt in all_locations:
            print(f"Bot: Using closest location '{alt}' instead of '{location}'.")
            return alt, None
        match = get_close_matches(location, all_locations, n=1, cutoff=0.65)
        if match:
            print(f"Bot: Approximated '{location}' as '{match[0]}'.")
            return match[0], None
        print(f"Bot: Could not resolve location '{location}'.")
        return location, None

    # CASE 2: Environment only
    elif requested_env and not location:
        candidate_locs = sorted({p.location for p in properties if p.environment.lower() == requested_env.lower()})
        if not candidate_locs:
            print(f"Bot: No cities found with environment '{requested_env}'.")
            return None, requested_env
        if len(candidate_locs) == 1:
            return candidate_locs[0], requested_env

        prompt = (
            f"The user asked for a vacation in environment '{requested_env}'. "
            f"My database contains these locations with that environment: {candidate_locs}. "
            "Which is the best known or closest option? Return ONLY one location."
        )
        alt = llm_call(prompt, api_key=api_key, sys_prompt="You are a geographic resolver.")
        if alt and alt in candidate_locs:
            return alt, requested_env
        return candidate_locs[0], requested_env

    # CASE 3: Both location + environment
    elif location and requested_env:
        loc_envs = {p.environment for p in properties if p.location == location}
        if requested_env not in loc_envs:
            candidate_locs = sorted({p.location for p in properties if p.environment.lower() == requested_env.lower()})
            if candidate_locs:
                prompt = (
                    f"The user asked for '{location}' with a '{requested_env}' environment. "
                    f"My database has these locations with '{requested_env}': {candidate_locs}. "
                    f"Which is geographically closest to '{location}'? Return ONLY the location name."
                )
                alt = llm_call(prompt, api_key=api_key, sys_prompt="You are a geographic resolver.")
                if alt and alt in candidate_locs:
                    print(f"Bot: Redirecting to nearest '{requested_env}' location '{alt}' instead of '{location}'.")
                    return alt, requested_env
                print(f"Bot: Redirecting to '{candidate_locs[0]}' for requested environment '{requested_env}'.")
                return candidate_locs[0], requested_env
            print(f"Bot: No cities found with '{requested_env}'. Keeping location '{location}'.")
            return location, None
        return location, requested_env

    return None, None

# ---------- LLM Date Parsing ----------
def llm_parse_date(user_input, api_key, model=MODEL, default_year=None):
    prompt = (
        f"Interpret the following date input from the user and return it in YYYY-MM-DD format. "
        f"If the year is missing, assume it is {default_year}. Only return the date. "
        f"User input: '{user_input}'"
    )
    result = llm_call(prompt, api_key=api_key, model=model)
    try:
        dt = datetime.strptime(result.strip(), "%Y-%m-%d").date()
        return dt
    except Exception:
        return None

# ---------- Validation ----------
def validate_and_reprompt(parsed):
    max_capacity = max(p.capacity for p in properties)
    all_prices = [p.price for p in properties]
    min_price, max_price = min(all_prices), max(all_prices)

    if parsed.get("group_size") and parsed["group_size"] > max_capacity:
        print(f"Bot: Group size {parsed['group_size']} exceeds max capacity {max_capacity}.")
        parsed["group_size"] = max_capacity

    budget = parsed.get("budget") or parsed.get("price_max")
    if budget and (budget < min_price or budget > max_price):
        parsed["budget"] = parsed["price_max"] = min(max(budget, min_price), max_price)
    return parsed

# ---------- Main Parser ----------
def llm_parse(model=MODEL, temperature=0.7):
    import json

    api_key = input("Enter API key(not a free model! will return error if no balance): ").strip()
    user_prompt = input("Bot: What kind of property are you looking for? ").strip()
    if not user_prompt:
        return {"error": "No input provided"}

    # Initial LLM parse
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature
    }
    r = requests.post(
        API_ENDPOINT_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json=payload,
        timeout=60
    )
    if r.status_code != 200:
        return {"error": f"HTTP {r.status_code}", "details": r.text}

    data = r.json()
    content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")

    # Safe JSON parse
    try:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        parsed = json.loads(match.group(0)) if match else {}
    except Exception:
        parsed = {}

    # Location resolution
    mapped_loc, mapped_env = map_location_to_db(
        parsed.get("location"), ALL_LOCATIONS, parsed.get("environment"), api_key=api_key
    )
    if not mapped_loc or mapped_loc not in ALL_LOCATIONS:
        print("Bot: Sorry, I couldn't resolve that location. Let's try again.\n")
        return llm_parse(model=model, temperature=temperature)

    parsed["location"] = mapped_loc
    if mapped_env is not None:
        parsed["environment"] = mapped_env

    # Group size fallback
    if not parsed.get("group_size"):
        try:
            parsed["group_size"] = int(input("Bot: How many people? ").strip())
        except:
            parsed["group_size"] = 1

    # Budget fallback
    if parsed.get("budget") is None and parsed.get("price_max") is None:
        budget_input = input("Bot: What is your budget? (e.g. 1000 or 100-2500): ").strip()
        if "-" in budget_input:
            try:
                low, high = map(int, budget_input.split("-"))
                parsed["price_min"], parsed["price_max"], parsed["budget"] = low, high, high
            except:
                pass
        else:
            try:
                value = int(re.sub("[^0-9]", "", budget_input))
                parsed["price_min"], parsed["price_max"], parsed["budget"] = 0, value, value
            except:
                pass

    # Dates
    start_input = parsed.get("start_date") or input("Bot: Start date? (e.g. Aug 25): ").strip()
    end_input = parsed.get("end_date") or input("Bot: End date? (e.g. Aug 30): ").strip()
    start_dt = llm_parse_date(start_input, api_key, default_year=2025)
    end_dt = llm_parse_date(end_input, api_key)

    if not start_dt:
        start_dt = datetime.today().date() + timedelta(days=1)
    if not end_dt or end_dt <= start_dt:
        end_dt = start_dt + timedelta(days=1)

    parsed["start_date"], parsed["end_date"] = start_dt.isoformat(), end_dt.isoformat()
    parsed["dates"] = [(start_dt + timedelta(days=i)).isoformat() for i in range((end_dt - start_dt).days + 1)]

    # Normalize synonyms
    parsed = normalize_features_and_tags(parsed, api_key)
    parsed = normalize_env_and_type(parsed, api_key)
    parsed = validate_and_reprompt(parsed)

    # Ensure required keys exist
    if not parsed.get("location"):
        parsed["location"] = mapped_loc
    if not parsed.get("group_size"):
        parsed["group_size"] = 1
    if not parsed.get("budget") and not parsed.get("price_max"):
        parsed["budget"] = parsed["price_max"] = 999999
    if not parsed.get("start_date"):
        parsed["start_date"] = start_dt.isoformat()
    if not parsed.get("end_date"):
        parsed["end_date"] = end_dt.isoformat()
    if "features" not in parsed:
        parsed["features"] = []
    if "tags" not in parsed:
        parsed["tags"] = []
    if "environment" not in parsed:
        parsed["environment"] = None
    if "type" not in parsed:
        parsed["type"] = None

    print("Bot: Final request dictionary:")
    print(parsed)
    return parsed
