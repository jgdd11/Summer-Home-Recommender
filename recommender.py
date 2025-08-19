import pandas as pd
def recommendation_logic(property_list,user_req):
    df = pd.DataFrame(property_list) #load property_list as dataframe

    #assign location a score 1 if location matches, otherwise 0

    #assign capacity a score 1 if a property can hold that group size, otherwise 0
    #group_size <= property capacity

    #assign availability a score 1 if the property is available during that period, otherwise 0

    #assign price a score 1 if the price is at or below budget, otherwise 0
    #price <= budget

    #assign environment a score 1 if environment matches, otherwise 0

    #assign feature a score 1 if feature matches, otherwise 0

    #assign property scoe 0 if location, capacity or availability is 0

    #calculate property score using weighted average

    #rank property by property score

    #display top N
    pass