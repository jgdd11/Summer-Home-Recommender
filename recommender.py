import pandas as pd
import json
from datetime import datetime, date, timedelta
from typing import Union
from properties import Property


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

    print(f"There are {df.shape[0]} properties in the database.") #print number of rows in the data frame, can be used to check if properties that don't match have been removed

    # load user requirement
    required_keys = [
        "location", "group_size", "start_date", "end_date", "budget",
        "budget_wt", "enviro_wt", "feature_wt", "tags_wt"
    ]
    for key in required_keys:
        if key not in user_req:
            raise KeyError(f"Missing required user requirement key: '{key}'")

    user_location = user_req["location"]
    group_size = user_req["group_size"]
    start_date = datetime.strptime(user_req["start_date"], "%Y-%m-%d").date() 
    end_date = datetime.strptime(user_req["end_date"], "%Y-%m-%d").date()
    budget = user_req["budget"]
    user_features = user_req["features"]
    user_environment = user_req["environment"]
    user_tags = user_req["tags"]

    # load and normalize weights of each attribute
    total_wt = user_req["budget_wt"] + user_req["enviro_wt"] + user_req["feature_wt"] + user_req["tags_wt"]
    norm_budget_wt = round(user_req["budget_wt"] / total_wt, 3)
    norm_enviro_wt = round(user_req["enviro_wt"] / total_wt, 3)
    norm_feature_wt = round(user_req["feature_wt"] / total_wt, 3)
    norm_tag_wt = round(user_req["tags_wt"] / total_wt, 3)

    # drop properties that don't match location or group size
    df = df[df["location"].str.contains(user_location, na=False)]
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

    # print number of rows in the data frame again, number should be less than the original row num, showing some rows have been dropped
    print(f"There are {df.shape[0]} properties that match your travel location, group size, and travel dates.")

    # calculate property score
    for idx, row in df.iterrows():
        score = 0

        if row["price"] <= budget:
            score += 1 * norm_budget_wt
        if row["environment"] == user_environment:
            score += 1 * norm_enviro_wt
        
        if len(user_features) > 0:
            user_features_lower = {f.lower() for f in user_features}
            property_features_lower = {f.lower() for f in row["features"]}
            feature_score = len(user_features_lower.intersection(property_features_lower)) / len(user_features)
            score += feature_score * norm_feature_wt
        else: 
            score += 1 * norm_feature_wt

        if len(user_tags) > 0:
            user_tags_lower = {f.lower() for f in user_tags}
            property_tags_lower = {f.lower() for f in row["tags"]}
            tag_score = len(user_tags_lower.intersection(property_tags_lower)) / len(user_tags)
            score += tag_score * norm_tag_wt
        else: 
            score += 1 * norm_tag_wt

        df.at[idx, "score"] = round(score,3)

    # rank property by property score
    df = df.sort_values(by="score", ascending=False)

    df = df[["id", "score", "price", "features", "environment", "tags"]]
    df = df.reset_index(drop=True)

    # display top 10
    print(df.head(10))
    recommended_df = df.head(10)
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


# below is for testing
# if __name__ == "__main__":

#     # input = "properties.json"
#     # input = pd.read_json("properties.json")
#     with open("properties.json", "r", encoding="utf-8") as f:
#         data = json.load(f)
#         input = [Property.from_dict(p) for p in data]

#     user_req = {'location': 'Toronto',
#             'environment': 'urban',
#             'group_size': 5,
#             'budget': 300,
#             'start_date': '2023-08-20',
#             'end_date': '2023-08-23',
#             'features': ['luxury', 'loft'],
#             'tags': ['city center'],
#             'dates': ['2023-08-20', '2023-08-21', '2023-08-22', '2023-08-23'],
#             'price_max': 300,
#             'price_min': 0,
#             'budget_wt': 0.3448275862068966,
#             'enviro_wt': 0.20689655172413793,
#             'feature_wt': 0.2413793103448276,
#             'tags_wt': 0.20689655172413793
#         }

#     recommendation_logic(input, user_req)
