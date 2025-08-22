import pwinput
import json
import hashlib
import re
from llm import llm_parse
from recommender import recommendation_logic
from properties import PropertiesController
from datetime import date
import json

class User:
    def __init__(self, username, password, name, email, reservations=None, preferences=None, attempts=0):
        self.username = username
        self.password = password if password else ""  # store hashed password later
        self.name = name
        self.email = email
        self.reservations = reservations if reservations is not None else []
        self.preferences = preferences or {}
        self.attempts = attempts

    # crypt user's pwd, since cannot store plain text of pwd in database
    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    # verify if user set a strong pwd
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

    # set user pwd
    def set_password(self):
        while True:
            password = pwinput.pwinput(
                "Create a password (8 chars, 1 capital, 1 number, 1 special): ", mask="*"
            )
            if not User.is_strong_password(password):  # check if is strong pwd
                print("Password does not meet requirements.")
                continue
            confirm = pwinput.pwinput("Confirm your password: ", mask="*")
            if password != confirm:  # check if two times input are the same
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

    def set_preferences(self):
        def get_weight(prompt):
            while True:
                try:
                    value = float(input(prompt))
                    if 0 <= value <= 10:
                        return value
                    else:
                        print("Please enter a number between 0 and 10.")
                except ValueError:
                    print("Invalid input. Please enter a number between 0 and 10.")

        print("We're just going to ask a few questions to get to know you better.")
        print("Please enter a number, 0-10, for how important each feature is.")
        print("0 means not important at all and 10 means this preference is a must-have.")

        budget = get_weight("How important is budget to you? ")
        enviro = get_weight("How important is environment to you? ")
        feature = get_weight("How important is it that you get your desired features? ")
        tag = get_weight("How important is it that the property has the tags you've requested? ")

        total = budget + enviro + feature + tag
        if total == 0:
            print("All preferences were zero, setting equal importance to each category.")
            total = 4
            budget = enviro = feature = tag = 1

        # setting preference as ratio percentage
        self.preferences = {
            "budget_wt": budget / total,
            "enviro_wt": enviro / total,
            "feature_wt": feature / total,
            "tags_wt": tag / total
        }

        print("Preferences set.")

    def check_password(self, password):
        return self.password == User.hash_password(password)
    
    def view_account_details(self):
        print(f"Name: {self.name}")
        print(f"Username: {self.username}")
        print(f"Email: {self.email}")
        print(f"Reservations: {self.reservations}")
        print(f"Preferences: {self.preferences}")

    def view_reservations(self):
        if not self.reservations:
            print("No reservations made yet.")
            return []
        for reservation in self.reservations:
            print(reservation)
        return self.reservations

    # connect to recommender.py and properties.py, to get recommended properties
    def get_recommendations(self, user_manager):
        # Get LLM output
        llm_output = llm_parse()
        
        # Merge with user preferences
        combined_input = {**llm_output, **self.preferences}
        print("Bot: Combined input for recommendations:", combined_input)
        
        # Get recommended properties
        pc = PropertiesController()
        properties = pc.load_properties()
        recommendations = recommendation_logic(properties, combined_input)
        
        while True:
            reserve = input("Bot: Would you like to make a reservation for any of these? (Y/N): ").strip().lower()
            if reserve in {"y", "n", "yes", "no"}:
                break
            print("Bot: Please enter Y, N, Yes, or No.")

        if reserve in {"y", "yes"}:
            self.make_reservation(recommendations, llm_output["start_date"], llm_output["end_date"], pc, user_manager)

    def make_reservation(self, recommended_properties, start_date, end_date, controller: PropertiesController, user_manager):
        decision = input("Please enter the ID of the property you would like to reserve: ").strip()
        try:
            decision = int(decision)
        except ValueError:
            print("Bot: Invalid ID. Reservation cancelled.")
            return

        recommended_property = next((p for p in recommended_properties if p.id == decision), None)
        if not recommended_property:
            print("Bot: No property found with that ID. Reservation cancelled.")
            return

        # Add reservation to user
        self.reservations.append({"id": recommended_property.id, "start": start_date, "end": end_date})

        # Update property booked dates
        prop = controller.find_by_id(decision)
        if not prop:
            print("Bot: Could not find property in master list. Reservation cancelled.")
            return

        start_date_obj = date.fromisoformat(start_date)
        end_date_obj = date.fromisoformat(end_date)
        prop.add_dates(start_date_obj, end_date_obj)

        # Save updated properties and users
        controller.save_properties()
        user_manager.save_users()

        print(f"Bot: Property {prop.id} successfully reserved from {start_date} to {end_date}.")


    def delete_reservation(self, user_manager):
        if not self.reservations:
            print("No reservations were made.")
            return

        print("You have made the following reservations:")
        self.view_reservations()

        try:
            id_to_cancel = int(input("Enter the ID of the property you would like to cancel: ").strip())
        except ValueError:
            print("Invalid ID (must be an integer).")
            return

        to_remove = next((r for r in self.reservations if r.get("id") == id_to_cancel), None)
        if not to_remove:
            print("No reservation with that ID.")
            return

        confirm = input(
            f"Are you sure you want to cancel the reservation with Property ID {id_to_cancel}? (Y/N): "
        ).strip().lower()

        if confirm != 'y':
            print("Cancellation aborted.")
            return

        # Remove reservation from user's list
        self.reservations.remove(to_remove)

        # Load properties.json
        with open("properties.json", "r") as f:
            properties = json.load(f)

        # Find the property and remove booked dates
        property_to_update = next((p for p in properties if p["id"] == id_to_cancel), None)
        if property_to_update:
            # Assuming reservation has 'start_date' and 'end_date' in "YYYY-MM-DD" format
            from datetime import datetime, timedelta

            start_date = datetime.strptime(to_remove["start"], "%Y-%m-%d")
            end_date = datetime.strptime(to_remove["end"], "%Y-%m-%d")

            # Generate all dates in the range
            dates_to_remove = [
                (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
                for i in range((end_date - start_date).days + 1)
            ]

            # Remove booked dates
            property_to_update["booked"] = [
                d for d in property_to_update.get("booked", []) if d not in dates_to_remove
            ]

            # Save updated properties back to JSON
            with open("properties.json", "w") as f:
                json.dump(properties, f, indent=4)

        # Save updated user data
        user_manager.save_users()
        print("Reservation cancelled and property dates freed.")


    def to_dict(self):
        return {
            "username": self.username,
            "password": self.password,
            "name": self.name,
            "email": self.email,
            "reservations": self.reservations,
            "preferences": self.preferences,
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
        user = User(username=username, password="", name=name, email=email, preferences=[]) #add a dictionary of weights 
        user.set_password() 
        user.set_preferences() 
        self.userdb.append(user) 
        self.save_users() 
        print(f"Account successfully created for '{username}'")

    def delete_user(self):
        pass
    
    def login(self):
        print("Welcome to All Rentals In Kind (ARIK)!")
        
        while True:
            username = input("Enter your username: ").strip()
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
                if user.attempts >= 5:  # if incorrect pwd input more than 5, preventing further trying
                    print("Exceeded password attempts.")
                    email = input("Enter your email to reset password or 1 to return: ").strip()
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
                
                password = pwinput.pwinput("Enter your password or 1 to go back: ", mask="*").strip()
                if password == "1":
                    break
                
                if user.check_password(password):
                    print(f"Login successful! Welcome, {user.name}.")
                    user.attempts = 0
                    self.save_users()
                    return user
                
                user.attempts += 1
                print(f"Incorrect password. Attempts: {user.attempts}")
