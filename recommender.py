import pandas as pd
import numpy as np
from datetime import timedelta

def recommendation_logic(property_list,user_req):

    #preferrably, dates need to load as date object, same for properties and user_req

    df = pd.DataFrame(property_list) #load property_list as dataframe
    print(df.head(10)) 
    print(df.shape[0]) #print number of rows in the data frame, can be used to check if properties that don't match have been removed

    #load user requirement
    user_location = user_req["location"]
    group_size = user_req["group_size"]
    start_date = user_req["start_date"] 
    end_date = user_req["end_date"]
    budget_low = user_req["budget_low"]
    budget_high = user_req["budget_high"]
    user_features = user_req["features"]
    user_environment = user_req["environment"]
    user_tags = user_req["tags"]
    budget_wt = user_req["budget_wt"]
    enviro_wt = user_req["enviro_wt"]
    feature_wt = user_req["feature_wt"]
    tags_wt = user_req["tags_wt"]


    #drop properties that don't match location or group size
    df = df[df["location"] == user_location] 
    df = df[df["capacity"] < group_size] 

    
    
    #the following portion of the code doesn't work, need to debug
    try:
        drop_dates = set(pd.date_range(start_date, end_date))
        df = df[~df["booked_dates"].apply(lambda lst: bool(set(lst) & drop_dates))]
    except TypeError:
        current_date = start_date
        while current_date <= end_date:
            df = df[~df["booked_dates"].apply(lambda lst: current_date in lst)]
            current_date += timedelta(days=1)

    print(df.shape[0]) #print number of rows in the data frame again, number should be less than the original row num, showing some rows have been dropped


    

    #assign price a score 1 if the price matches, otherwise 0
    #price falls within the budget range

    #assign environment a score 1 if environment matches, otherwise 0

    #assign feature a score 1 if feature matches, otherwise 0

    #assign property scoe 0 if location, capacity or availability is 0

    #calculate property score using weighted average

    #rank property by property score

    #display top N
    pass

"""
Recommendation Logic
- input property_list: list[Property]
- user_preferences: dict()
- user_weights: list[int], default [0.2, 0.1, 0.2, 0.5]

# hard filter: property has to match user requirement, drop otherwise

# normalize weight
# make sure weights add up to 1

# assigning weight and score for user preferences
for property in property_list:
    property_score = 0
    for item in (type, features, tags, environment):
        num_match = number of keywords that property matches user preference
        num_user_input = number of keywords from user inputs
        tmp_score = num_match / num_user_input
        property_score += tmp_score * weights[item]
    property.score = property_score

# sort by score and display top 5 properties
# show attributes and score of each property
"""
