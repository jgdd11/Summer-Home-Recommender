import pandas as pd

def recommendation_logic(property_list,user_req):
    df = pd.DataFrame(property_list) #load property_list as dataframe

    #kill properties that are 
    # 1) in the wrong location, 
    # 2) capacity is below group size
    # 3) unavailable

    

    #assign price a score 1 if the price matches, otherwise 0
    #price falls within the budget range

    #assign environment a score 1 if environment matches, otherwise 0

    #assign feature a score 1 if feature matches, otherwise 0

    #assign property scoe 0 if location, capacity or availability is 0

    #calculate property score using weighted average

    #rank property by property score

    #display top N
    pass