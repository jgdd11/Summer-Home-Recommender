import pwinput
import json
import hashlib
import re

def load_userdb():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def is_strong_password(password):
    """
    Check if the password meets the following criteria:
    - At least 8 characters
    - At least 1 uppercase letter
    - At least 1 number
    - At least 1 special character
    """
    if len(password) < 8:
        return False

    has_upper = re.search(r"[A-Z]", password)
    has_number = re.search(r"\d", password)
    has_special = re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)

    return all([has_upper, has_number, has_special])

def create_user(userdb):
    name = input("Please enter your name")
    username = input("Please enter your desired username: ")
    while True:
        password = pwinput.pwinput("Create a password with 8 characters, 1 capital letter, 1 number, and 1 special character: ", mask="*")
        password_confirm = pwinput.pwinput("Confirm your password: ", mask="*")
        if not is_strong_password(password):
            print("Please ensure your password has at least 8 characters, 1 capital letter, 1 number, and 1 special character (!@#$%^&*(),.?\":|<> are special characters)")
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

def login():
    userdb = load_userdb()
    while True:
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

login()

    
