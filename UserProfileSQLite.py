import sqlite3

def setup_database():
    conn = sqlite3.connect('user_profiles.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            group_size INTEGER NOT NULL,
            preferred_environment TEXT NOT NULL,
            budget_low INTEGER NOT NULL,
            budget_high INTEGER NOT NULL,
            travel_date_start TEXT NOT NULL  -- store date in ISO format YYYY-MM-DD
            travel_date_end TEXT NOT NULL  -- store date in ISO format YYYY-MM-DD
        )
    ''')
    conn.commit()
    conn.close()

# function 2: create - prompt user input and insert into database
def create_user():
    pass
    # user_name    
    #      c.execute("""
    #         INSERT INTO profiles (name, group_size, preferred_environment, budget_low, budget_high, travel_date_start, travel_date_end)
    #         VALUES (?, ?, ?, ?, ?, ?, ?)
    #         """, ("Alice Johnson", 8, "Mountain", 100, 250, "2025-10-01", "2025-10-20"))

# function 3: view - return user list
def view_all_users():
    pass
    #     c.execute("SELECT * FROM profiles")
    #     for row in c.fetchall():
    #         print(row)

# function 4: view - return attribute of one user
def view_user():
    pass


# function 5: edit profile - prompt user input and update database
def edit_user():
    pass

# function 6: delete profile
def delete_user():
    pass
