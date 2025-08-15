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

# User sets a password and follows the standard procedure to do so
def set_password(username = None, userdb = None):
    while True:
        password = pwinput.pwinput("Create a password (8 chars, 1 capital, 1 number, 1 special): ", mask="*")
        if not is_strong_password(password):
            print("Please ensure your password meets the requirements.")
            continue
        password_confirm = pwinput.pwinput("Confirm your password: ", mask="*")
        if password != password_confirm:
            print("Passwords do not match. Please try again.")
            continue
        break

    if username is not None and userdb is not None:
        user = next((u for u in userdb if u["username"] == username), None)
        if user:
            user["password"] = hash_password(password)
            with open("users.json", "w") as f:
                json.dump(userdb, f, indent=4)
            print("Password successfully changed.")
        else:
            print(f"User '{username}' not found.")
    else:
        return hash_password(password)

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def set_email(username = None, userdb = None):
    while True:
        email = input("Please enter an email: ")
        if not is_valid_email(email):
            print("Please enter a valid email.")
        else:
            break
    if username is not None and userdb is not None:
        user = next((u for u in userdb if u["username"] == username), None)
        if user:
            user["email"] = email
            with open("users.json", "w") as f:
                json.dump(userdb, f, indent=4)
            print("Email successfully updated.")
        else:
            print(f"User '{username}' not found.")
    else:
        return email
        
# Follows standard procedure to create user and add them to users.json
def create_user(userdb):
    name = input("Please enter your name: ")
    username = input("Please enter your desired username: ")
    email = set_email()
    password = set_password()

    new_user = {
        "username": username,
        "password": hash_password(password),
        "name": name,
        "email": email,
        "reservations": [],
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
        print("Welcome to [INSERT CLEVER APP NAME HERE]!")
        username = input("Enter your username: ")
        userdata = next((user for user in userdb if user["username"] == username), None)

        if not userdata:
            while True:
                yesno = input("Username not found. Would you like to create an account? (Y or N) ").lower()
                if yesno in ("y", "yes"):
                    create_user(userdb)
                    break
                elif yesno in ("n", "no"):
                    print("Returning to login screen.")
                    break
                else:
                    print("Please enter Y or N.")
            continue

        userdata.setdefault("attempts", 0)

        while True:
            if userdata["attempts"] >= 5:
                print("Exceeded password attempts.")
                while True:
                    email = input("Please enter your email to reset your password or type 1 to return to login screen: ")
                    if email == "1":
                        print("Returning to login screen.")
                        break
                    if email == userdata["email"]:
                        userdata["password"] = set_password(username, userdb)
                        userdata["attempts"] = 0
                        print("Password reset successful. Please log in again.")
                        break
                    else:
                        print("Incorrect email. Please try again or type 1 to return to login screen.")
                break 
            password = pwinput.pwinput("Enter your password or type 1 to go back: ", mask="*")
            
            if password == "1":
                break

            if userdata["password"] == hash_password(password):
                print("Login successful!")
                userdata["attempts"] = 0
                return userdata

            userdata["attempts"] += 1
            print(f"Incorrect password. Attempts: {userdata['attempts']}")

login()