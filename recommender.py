import pandas as pd

def recommendation_logic(property_list,user_req):
    df = pd.DataFrame(property_list) #load property_list as dataframe

    #function #1: assign location a score 1 if location matches, otherwise 0

    #function #2: assign group_size a score 1 if a property can hold the number of people, otherwise 0
    #group_size <= property capacity

    #function #3: assign date a score 1 if the property is available during that period, otherwise 0


    pass