import pwinput
import json
import hashlib
import re

class User:
    def __init__(self, username, password, name, email, reservations=None, attempts=0):
        self.username = username
        self.password = password if password else ""  # store hashed password later
        self.name = name
        self.email = email
        self.reservations = reservations if reservations is not None else []
        self.attempts = attempts

    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def is_strong_password(password):
        if len(password) < 8:
            return False
        has_upper = re.search(r"[A-Z]", password)
        has_number = re.search(r"\d", password)
        has_special = re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)
        return all([has_upper, has_number, has_special])

    @staticmethod
    def is_valid_email(email):
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return re.match(pattern, email) is not None

    def set_password(self):
        while True:
            password = pwinput.pwinput(
                "Create a password (8 chars, 1 capital, 1 number, 1 special): ", mask="*"
            )
            if not User.is_strong_password(password):
                print("Password does not meet requirements.")
                continue
            confirm = pwinput.pwinput("Confirm your password: ", mask="*")
            if password != confirm:
                print("Passwords do not match.")
                continue
            break
        self.password = User.hash_password(password)
        print("Password successfully set.")

    def set_username(self, userdb):
        while True:
            username = input("Enter your new username: ").strip()
            if not username:
                print("Username cannot be empty.")
                continue
            if any(u.username == username and u.email != self.email for u in userdb):
                print("Username already in use by another user.")
                continue
            break
        self.username = username
        print("Username successfully updated.")

    def set_email(self, userdb):
        while True:
            email = input("Enter your new email: ")
            if not User.is_valid_email(email):
                print("Invalid email format.")
                continue
            if any(u.email == email and u.username != self.username for u in userdb):
                print("Email already in use by another user.")
                continue
            break
        self.email = email
        print("Email successfully updated.")

    def check_password(self, password):
        return self.password == User.hash_password(password)
    
    def view_account_details(self):
        print(f"Name: {self.name}")
        print(f"Username: {self.username}")
        print(f"Email: {self.email}")

    def view_reservations(self):
        for reservation in self.reservations:
            print(reservation)
        return self.reservations

    def to_dict(self):
        return {
            "username": self.username,
            "password": self.password,
            "name": self.name,
            "email": self.email,
            "reservations": self.reservations,
            "attempts": self.attempts,
        }


class UserManager:
    def __init__(self):
        self.filename = "users.json"
        self.userdb = self.load_users()

    def load_users(self):
        try:
            with open(self.filename, "r") as f:
                data = json.load(f)
                return [User(**u) for u in data]
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_users(self):
        with open(self.filename, "w") as f:
            json.dump([u.to_dict() for u in self.userdb], f, indent=4)

    def find_user(self, username):
        return next((user for user in self.userdb if user.username == username), None)

    def create_user(self):
        name = input("Enter your name: ")

        while True:
            username = input("Enter your desired username: ").strip()
            if not username:
                print("Username cannot be empty.")
                continue
            if self.find_user(username):
                print("Username already taken. Try another.")
                continue
            break

        while True:
            email = input("Enter your email: ")
            if not User.is_valid_email(email):
                print("Invalid email format.")
                continue
            if any(u.email == email for u in self.userdb):
                print("Email already in use. Try another.")
                continue
            break

        user = User(username=username, password="", name=name, email=email)
        user.set_password()
        self.userdb.append(user)
        self.save_users()
        print(f"Account successfully created for '{username}'")

    def delete_user(self, user):
        confirm = input(f"Are you sure you want to delete your account, {user.username}? (Y/N): ").strip().lower()
        if confirm not in ("y", "yes"):
            print("Account deletion cancelled.")
            return False

        self.userdb = [u for u in self.userdb if u.username != user.username]
        self.save_users()
        print(f"Account '{user.username}' deleted successfully.")
        return True

    def login(self):
        while True:
            print("Welcome to [INSERT CLEVER APP NAME HERE]!")
            username = input("Enter your username: ")
            user = self.find_user(username)
            if not user:
                choice = input("Username not found. Create account? (Y/N): ").lower()
                if choice in ("y", "yes"):
                    self.create_user()
                    continue
                else:
                    print("Returning to login screen.")
                    continue

            user.attempts = getattr(user, "attempts", 0)

            while True:
                if user.attempts >= 5:
                    print("Exceeded password attempts.")
                    email = input("Enter your email to reset password or 1 to return: ")
                    if email == "1":
                        break
                    if email == user.email:
                        user.set_password()
                        user.attempts = 0
                        self.save_users()
                        print("Password reset successful. Log in again.")
                        break
                    else:
                        print("Incorrect email.")
                    continue

                password = pwinput.pwinput(
                    "Enter your password or 1 to go back: ", mask="*"
                )
                if password == "1":
                    break

                if user.check_password(password):
                    print("Login successful!")
                    user.attempts = 0
                    self.save_users()
                    return user

                user.attempts += 1
                print(f"Incorrect password. Attempts: {user.attempts}")