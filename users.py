import pwinput
import json
import hashlib
import re

# Loads the users.json database
def load_userdb():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Hashcodes password for added security
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Checks if a password meets desired criteria
def is_strong_password(password):
    if len(password) < 8:
        return False

    has_upper = re.search(r"[A-Z]", password)
    has_number = re.search(r"\d", password)
    has_special = re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)

    return all([has_upper, has_number, has_special])

# Follows standard procedure to create user and add them to users.json
def create_user(userdb):
    name = input("Please enter your name: ")
    username = input("Please enter your desired username: ")
    while True:
        password = pwinput.pwinput("Create a password (8 chars, 1 capital, 1 number, 1 special): ", mask="*")
        password_confirm = pwinput.pwinput("Confirm your password: ", mask="*")
        if not is_strong_password(password):
            print("Please ensure your password meets the requirements.")
            continue
        if password != password_confirm:
            print("Passwords do not match. Please try again.")
            continue
        break

    new_user = {
        "username": username,
        "password": hash_password(password),
        "name": name,
        "reservations": []
    }
    userdb.append(new_user)
    with open("users.json", "w") as f:
        json.dump(userdb, f, indent=4) 
    print(f"Account successfully created for '{username}'")

# Allows a user to login and returns their info if they exist in the users.json, if not
# prompts them to create a user
def login():
    userdb = load_userdb()
    while True:
        print("Welcome to [INSERT COOL COMPANY NAME HERE]!")
        username = input("Enter your username: ")
        userdata = next((user for user in userdb if user["username"] == username), None)

        if not userdata:
            print("Username not found. Please create account.")
            create_user(userdb)
            continue 

        while True:
            password = pwinput.pwinput("Enter your password or type 1 to go back: ", mask="*")
            if password == "1":
                break 
            if userdata["password"] == hash_password(password):
                print("Login successful!")
                return userdata
            print("Incorrect password. Try again.")

