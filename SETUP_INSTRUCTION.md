# Setup Instructions

## Prerequisites

- Download or clone this project
- Python 3.8+
- An LLM API key to LLM model gpt-4o-mini (OpenRouter/OpenAI)


## Setup Python Virtual Environment

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Upgrade pip and install dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Configuration / Data files

- `properties.json` — stores property records used by the recommender. Each record must follow the shape expected by `properties.Property` (see `properties.py`). The repository includes a `properties.json` file but it may need valid property entries.
- `users.json` — contains user accounts. Sample users exist in the repo.

## Running This Project

Start the main program from the repository root:

```bash
source .venv/bin/activate   # if not already active
python main.py
```
