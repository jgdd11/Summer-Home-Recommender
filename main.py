from users import UserManager

def main():
    manager = UserManager()
    logged_in_user = manager.login()
    if logged_in_user:
        print(f"Welcome, {logged_in_user.name}!")
    else:
        print("No user logged in.")

if __name__ == "__main__":
    main()
