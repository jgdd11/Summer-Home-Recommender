import requests, getpass, json

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-chat"  # try alternatives if needed

# Safely input your key (won't echo in Colab)
API_KEY = getpass.getpass("Enter your OpenRouter API key (input is hidden): ").strip()
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

SYSTEM_PROMPT = (
    "You are a helpful assistant for an Airbnb-like vacation property search. "
    "Given PROPERTIES (JSON) and a USER REQUEST, return JSON with keys: "
    "'tags' (list[str]) and optionally 'property_ids' (list[int]). Return ONLY valid JSON."
)

def llm_search(properties, user_prompt, model, temperature):
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "PROPERTIES:\n" + json.dumps(properties) +
                    "\n\nUSER REQUEST:\n" + user_prompt +
                    "\n\nRespond ONLY with JSON: {\"tags\": [...], \"property_ids\": [...]}"
                ),
            },
        ],
        "temperature": temperature,
    }
    r = requests.post(OPENROUTER_URL, headers=HEADERS, json=payload, timeout=60)
    if r.status_code != 200:
        return {"error": f"HTTP {r.status_code}", "details": r.text}
    data = r.json()
    content = (data.get("choices") or [{}])[0].get("message", {}).get("content")
    if not content:
        return {"error": "Empty response", "raw": data}
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Fallback: try to extract JSON substring
        s, e = content.find("{"), content.rfind("}")
        if s != -1 and e != -1 and e > s:
            try:
                return json.loads(content[s:e+1])
            except json.JSONDecodeError:
                return {"error": "Non-JSON content", "raw": content}
        return {"error": "Non-JSON content", "raw": content}

# Example single-turn usage (optional quick test)
example_request = "Cozy place by the lake with a fireplace under $220"
subset = properties[:12]  # send fewer for cheaper tokens
print("Querying model... (uses your API key)")
resp = llm_search(subset, example_request, model = MODEL, temperature=0.7)
print(resp)

def combine_llm_and_scores(scored_df, llm_resp, top_k):
    if not isinstance(llm_resp, dict) or "error" in llm_resp:
        return None
    ids = llm_resp.get("property_ids")
    if ids:
        sub = scored_df[scored_df["property_id"].isin(ids)].copy()
        if sub.empty:
            return scored_df.head(top_k)[["property_id", "location", "type", "price_per_night", "match_score"]]
        return sub.sort_values("match_score", ascending=False).head(top_k)[["property_id", "location", "type", "price_per_night", "match_score"]]
    else:
        # No IDs provided: just show our vectorized top matches
        return scored_df.head(top_k)[["property_id", "location", "type", "price_per_night", "match_score"]]

print("Type 'exit' to quit.")
while True:
    q = input("You: ").strip()
    if q.lower() == "exit":
        print("Bot: Have a great vacation! 🏖️")
        break
    resp = llm_search(properties, q, model = MODEL, temperature=0.7)
    print(resp)
    if isinstance(resp, dict) and "error" in resp:
        print("Bot (error):", resp.get("error"))
        print(resp.get("details", resp.get("raw", ""))[:500])
        continue
    print("Bot (raw):", resp)
    combined = combine_llm_and_scores(scored, resp, top_k=5)
    if combined is None:
        print("Bot: Couldn't parse a useful response; showing vectorized top-5:")
        print(scored.head(5)[["property_id", "location", "type", "price_per_night", "match_score"]])
    else:
        print("Bot: Top suggestions (by our numeric score):")
        print(combined)