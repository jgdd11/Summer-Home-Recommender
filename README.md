# User Reservation Management System

This reservation system has the nice name of 'All Rentals In Kind'. We Seek Experiences,  Navigates Destinations-Every Retreat Offers Value, Inspires Connections and Happiness. It aims to provide a user-friendly interface for managing user accounts and reservations. Users can log in, view and modify their reservations, update account details, and delete their accounts.


```
## Features

- User authentication (login)
- View current reservations
- Make new reservations based on recommendations
- Delete existing reservations
- View and update account details:
  - Username
  - Email
  - Password
  - Preferences
- Delete user account
- Logout functionality
- **AI-powered property search assistance** using OpenRouter/OpenAI API
```

```
## Recommendation Logic

The system includes a recommendation engine that suggests properties based on user preferences and requirements. Here's an overview:

- **Input Data**: Properties can be loaded from a JSON file, a list of `Property` objects, or a DataFrame.
- **User Requirements**: Specifies location, group size, travel dates, budget, features, environment, and tags.
- **Filtering**:
  - Match location and capacity
  - Exclude properties unavailable during the desired travel dates
- **Scoring**:
  - Budget compatibility
  - Environmental match
  - Features overlap
  - Tags overlap
- **Ranking**:
  - Properties are scored based on weighted criteria
  - Top 10 recommendations are returned

This process helps users find the most suitable properties aligned with their preferences and constraints.
```

```
## AI-Powered Property Search Assistance (`llm.py`)

The `llm.py` script integrates with an LLM API (OpenRouter or OpenAI) to interpret natural language user requests into structured search parameters. Here's how it works:

- **User Prompt**: Asks the user to describe the desired property in natural language.
- **API Interaction**: Sends the prompt to the LLM API with a system prompt emphasizing output format.
- **Response Parsing**: Attempts to evaluate the LLM's output into a Python dictionary containing fields such as:
  - `location`, `environment`, `group_size`, `budget`, `price_min`, `price_max`, `features`, `tags`, `start_date`, `end_date`.
- **Field Completion**:
  - If the LLM response lacks certain fields, the script interactively prompts the user for missing information.
  - Parses dates in various formats and expands the travel date range.
- **Output**: Returns a structured Python dictionary of search criteria, which can be used for property recommendation.

This AI-assisted process simplifies complex user inputs and enhances the search experience by understanding natural language descriptions.

## Requirements

- Python 3.x
- pandas
- requests

## Installation

1. Clone this repository or download the code files.
2. Install required packages:
```bash
pip install pandas requests
```
