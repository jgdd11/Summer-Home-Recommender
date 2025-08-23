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
                if alt and auto:
                    result.append(alt)
        return result
    parsed["features"] = process_list(parsed.get("features", []), ALL_FEATURES, "feature")
    parsed["tags"] = process_list(parsed.get("tags", []), ALL_TAGS, "tag")
    return parsed

def normalize_env_and_type(parsed, api_key):
    if parsed.get("environment") and parsed["environment"] not in ALL_ENVIRONMENTS:
        alt, auto = llm_normalize_term(parsed["environment"], ALL_ENVIRONMENTS, "environment", api_key=api_key)
        if alt and auto: parsed["environment"] = alt
    if parsed.get("type") and parsed["type"] not in ALL_TYPES:
        alt, auto = llm_normalize_term(parsed["type"], ALL_TYPES, "property type", api_key=api_key)
        if alt and auto: parsed["type"] = alt
    return parsed

# ---------- Location & Environment ----------
def map_location_to_db(location, all_locations, requested_env=None, api_key=None):
    """
    Map location and environment to DB.
    Cases:
    1. Location given, no environment → validate location against DB. 
       If missing, ask LLM to resolve to closest DB location.
    2. Environment given, no location → pick from DB locations with that environment.
       If multiple candidates, prompt user to choose.
    3. Both given → validate compatibility (keep your existing logic).
    """

    # --- CASE 1: Location given, no environment ---
    if location and not requested_env:
        if location in all_locations:
            # Use as is
            loc_envs = {p.environment for p in properties if p.location == location}
            return location, next(iter(loc_envs))  # pick any env available
        else:
            # Ask LLM to pick closest match from DB
            prompt = (
                f"The user asked for '{location}' as a vacation location. "
                f"My database contains these valid cities/regions: {all_locations}. "
                "Which one is the closest real-world match? Return ONLY the city/region name."
            )
            alt = llm_call(prompt, api_key=api_key, sys_prompt="You are a location resolver.")
            if alt and alt in all_locations:
                loc_envs = {p.environment for p in properties if p.location == alt}
                print(f"Bot: Using closest location '{alt}' instead of '{location}'.")
                return alt, next(iter(loc_envs))
            else:
                # fallback: fuzzy match
                match = get_close_matches(location, all_locations, n=1, cutoff=0.65)
                if match:
                    loc_envs = {p.environment for p in properties if p.location == match[0]}
                    print(f"Bot: Approximated '{location}' as '{match[0]}'.")
                    return match[0], next(iter(loc_envs))
                else:
                    print(f"Bot: Could not resolve location '{location}'.")
                    return location, None

    # --- CASE 2: Environment given, no location ---
    elif requested_env and not location:
        candidate_locs = sorted({p.location for p in properties if p.environment.lower() == requested_env.lower()})
        if not candidate_locs:
            print(f"Bot: No cities found with environment '{requested_env}'.")
            return None, requested_env
        elif len(candidate_locs) == 1:
            return candidate_locs[0], requested_env
        else:
            print(f"Bot: Multiple cities have environment '{requested_env}':")
            for i, loc in enumerate(candidate_locs, 1):
                print(f"{i}. {loc}")
            choice = input("Please choose a city by number: ").strip()
            try:
                idx = int(choice) - 1
                return candidate_locs[idx], requested_env
            except:
                return candidate_locs[0], requested_env  # fallback first

    # --- CASE 3: Both given (keep your old conflict resolution logic) ---
    elif location and requested_env:
        match = get_close_matches(location, all_locations, n=1, cutoff=0.75)
        mapped_loc = match[0] if match else location
        loc_envs = {p.environment for p in properties if p.location == mapped_loc}

        if requested_env not in loc_envs:
            choice = input(
                f"Your requested location '{mapped_loc}' does not have any properties with the '{requested_env}' environment.\n"
                "Which is more important? Type 'location' to keep location, or 'environment' to prioritize environment: "
            ).strip().lower()
            if choice == "location":
                mapped_env = next(iter(loc_envs))
                print(f"Bot: Keeping location '{mapped_loc}'. Environment set to '{mapped_env}'.")
                return mapped_loc, mapped_env
            else:
                candidate_locs = sorted({p.location for p in properties if p.environment.lower() == requested_env.lower()})
                if candidate_locs:
                    mapped_loc = candidate_locs[0]
                    print(f"Bot: Keeping environment '{requested_env}'. Location set to '{mapped_loc}'.")
                    return mapped_loc, requested_env
                else:
                    mapped_env = next(iter(loc_envs))
                    print(f"Bot: No cities found with '{requested_env}'. Keeping location '{mapped_loc}' with environment '{mapped_env}'.")
                    return mapped_loc, mapped_env

        return mapped_loc, requested_env

    return None, None


# ---------- LLM Date Parsing ----------
def llm_parse_date(user_input, api_key, model=MODEL, default_year=None):
    """Use LLM to parse natural language date into YYYY-MM-DD format. 
    If year is missing, use default_year."""
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
        # fallback: try parsing without year
        try:
            dt = datetime.strptime(user_input.strip(), "%b %d")
            if default_year:
                dt = dt.replace(year=default_year)
            return dt.date()
        except:
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
    api_key = input("Enter API key: ").strip()
    user_prompt = input("Bot: What kind of property are you looking for? ").strip()
    if not user_prompt: return {"error": "No input provided"}

    # Initial LLM parse
    payload = {"model": model, "messages": [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}], "temperature": temperature}
    r = requests.post(OPENROUTER_URL, headers={"Authorization": f"Bearer {api_key}"}, json=payload, timeout=60)
    if r.status_code != 200: return {"error": f"HTTP {r.status_code}", "details": r.text}
    data = r.json()
    content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
    try: parsed = eval(content) if content else {}
    except: parsed = {}

    if not parsed.get("location"):
        parsed["location"] = input("Bot: Please specify a location: ").strip()

    # Map location to DB & resolve environment conflicts
    parsed["location"], parsed["environment"] = map_location_to_db(
        parsed["location"], ALL_LOCATIONS, parsed.get("environment")
    )

    # Group size
    if not parsed.get("group_size"):
        try: parsed["group_size"] = int(input("Bot: How many people? ").strip())
        except: parsed["group_size"] = 1

    # Budget
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

    # Dates via LLM
    start_input = parsed.get("start_date") or input("Bot: Start date? (e.g. Aug 25): ").strip()
    end_input = parsed.get("end_date") or input("Bot: End date? (e.g. Aug 30): ").strip()

    # Start date defaults to 2025 if no year
    start_dt = llm_parse_date(start_input, api_key, default_year=2025)

    # End date: ensure first valid occurrence after start
    end_dt = llm_parse_date(end_input, api_key)
    if end_dt:
        if end_dt <= start_dt:
            # If parsed earlier or same, shift to next year
            end_dt = end_dt.replace(year=start_dt.year if end_dt.month > start_dt.month or (end_dt.month == start_dt.month and end_dt.day > start_dt.day) else start_dt.year + 1)
    else:
        end_dt = start_dt + timedelta(days=1)

    today = datetime.today().date()
    if not start_dt: start_dt = today + timedelta(days=1)
    if not end_dt: end_dt = start_dt + timedelta(days=1)

    parsed["start_date"], parsed["end_date"] = start_dt.isoformat(), end_dt.isoformat()
    parsed["dates"] = [(start_dt + timedelta(days=i)).isoformat() for i in range((end_dt - start_dt).days + 1)]

    # Normalize features, tags, environment, type
    parsed = normalize_features_and_tags(parsed, api_key)
    parsed = normalize_env_and_type(parsed, api_key)
    parsed = validate_and_reprompt(parsed)

    print("Bot: Final request dictionary:")
    print(parsed)
    return parsed
