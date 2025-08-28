import pandas as pd
import json
from datetime import datetime, date, timedelta
from typing import Union
from properties import Property

RECOMMEND_TOP_N = 10


# create date range generator
def daterange(start_date: date, end_date: date):
    days = int((end_date - start_date).days)
    for n in range(days):
        yield start_date + timedelta(n)


def recommendation_logic(properties: Union[str, list, pd.DataFrame], user_req: dict):
    """
    Recommendation logic
    """

    if isinstance(properties, str): # filename
        df = pd.read_json(properties)
    elif isinstance(properties, list) and all(isinstance(p, Property) for p in properties):
        df = pd.DataFrame([p.to_dict() for p in properties])
    elif isinstance(properties, pd.DataFrame):
        df = properties
    else:
        raise ValueError("Invalid properties input. Must be a list of Property objects, a DataFrame, or a JSON file path.")

    print(f"There are {df.shape[0]} properties in the database.")

    # load user requirement
    required_keys = [
        "location", "group_size", "start_date", "end_date",
        "budget_wt", "enviro_wt", "feature_wt", "tags_wt"
    ]

    # prompt user if their input is missing required fields
    for key in required_keys:
        if key not in user_req:
            raise KeyError(f"Missing required user requirement key: '{key}'")

    user_location = user_req["location"]
    if isinstance(user_location, str):
        user_location = [user_location]
    group_size = user_req["group_size"]
    start_date = datetime.strptime(user_req["start_date"], "%Y-%m-%d").date() 
    end_date = datetime.strptime(user_req["end_date"], "%Y-%m-%d").date()
    budget = user_req.get("budget", user_req.get("price_max"))
    if not budget:
        raise KeyError("Missing required user requirement key: 'budget' or 'price_max'")
    user_features = user_req.get("features")
    user_environment = user_req.get("environment")
    user_tags = user_req.get("tags")

    # load and normalize weights of each attribute
    total_wt = user_req["budget_wt"] + user_req["enviro_wt"] + user_req["feature_wt"] + user_req["tags_wt"]
    norm_budget_wt = round(user_req["budget_wt"] / total_wt, 3)
    norm_enviro_wt = round(user_req["enviro_wt"] / total_wt, 3)
    norm_feature_wt = round(user_req["feature_wt"] / total_wt, 3)
    norm_tag_wt = round(user_req["tags_wt"] / total_wt, 3)

    # drop properties that don't match location
    location_pattern = "|".join([str(loc) for loc in user_location])
    df = df[df["location"].str.contains(location_pattern, na=False, case=False)]

    # drop properties that don't match group size
    df = df[df["capacity"] >= group_size]

    # get days that need to be booked
    travel_dates = []
    for day in daterange(start_date, end_date):
        travel_dates.append(day)

    # drop rows that are unavailable during the travel_dates
    df["booked"] = df["booked"].apply(lambda dates: [pd.to_datetime(d).date() for d in dates])
    df = df[df["booked"].apply(
        lambda u: set(u).isdisjoint(set(travel_dates))
    )]

    #prompt user if no property in database matches their requirements
    if df.shape[0] == 0:
        print("No properties available that match your requirements.")
        return []

    # If properties are found, print the number of matching properties and calculate the score of the properties
    else:
        print(f"There are {df.shape[0]} properties that match your travel location, group size, and travel dates.")

        # initialize property score to 0
        df["score"] = 0.0
        for idx, row in df.iterrows():
            score = 0

            # full score if within budget, otherwise 0
            if row["price"] <= budget: # full score if within budget, otherwise 0
                score += 1 * norm_budget_wt

            # full score if no specific environment is requested or environment matches
            if user_environment is None or row["environment"] == user_environment: # full score if no specific environment is requested or environment matches
                score += 1 * norm_enviro_wt

            # full score if no specific features are requested, otherwise partial score based on matching features
            if user_features is not None and len(user_features) > 0:
                user_features_lower = {f.lower() for f in user_features}
                property_features_lower = {f.lower() for f in row["features"]}
                feature_score = len(user_features_lower.intersection(property_features_lower)) / len(user_features)
                score += feature_score * norm_feature_wt
            else: 
                score += 1 * norm_feature_wt

            # full score if no specific tags are requested, otherwise partial score based on matching tags
            if user_tags is not None and len(user_tags) > 0:
                user_tags_lower = {f.lower() for f in user_tags}
                property_tags_lower = {f.lower() for f in row["tags"]}
                tag_score = len(user_tags_lower.intersection(property_tags_lower)) / len(user_tags)
                score += tag_score * norm_tag_wt
            else: 
                score += 1 * norm_tag_wt
        
            # update the score in the dataframe
            df.at[idx, "score"] = round(score,3)*100

        # rank property by property score
        df = df.sort_values(by="score", ascending=False)

        df = df[["id", "score", "price", "features", "environment", "tags"]]
        df = df.reset_index(drop=True)

        # display top N
        print(df.head(RECOMMEND_TOP_N))
        recommended_df = df.head(RECOMMEND_TOP_N)
        recommended_properties = []

        for _, row in recommended_df.iterrows():
            recommended_properties.append(
                Property(
                    id=int(row["id"]),
                    location=row.get("location", ""),
                    type=row.get("type", ""),
                    price=float(row["price"]),
                    capacity=int(row.get("capacity", 0)),
                    environment=row.get("environment", ""),
                    features=list(row.get("features", [])),
                    tags=list(row.get("tags", [])),
                    booked=[d if isinstance(d, date) else pd.to_datetime(d).date() for d in row.get("booked", [])]
                )
            )

        return recommended_properties
