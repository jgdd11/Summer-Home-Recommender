from users import UserManager

def main():
    manager = UserManager()
    logged_in_user = manager.login()

    if not logged_in_user:
        print("No user logged in.")
        return

    print(f"Welcome, {logged_in_user.name}!")

    while True:
        print("\nAccount Menu:")
        print("1. Update Username")
        print("2. Update Email")
        print("3. Update Password")
        print("4. Delete Account")
        print("5. Logout")

        choice = input("Enter your choice (1-5): ").strip()

        if choice == "1":
            logged_in_user.set_username(manager.userdb)
            manager.save_users()
        elif choice == "2":
            logged_in_user.set_email(manager.userdb)
            manager.save_users()
        elif choice == "3":
            logged_in_user.set_password()
            manager.save_users()
        elif choice == "4":
            deleted = manager.delete_user(logged_in_user)
            if deleted:
                break  # exit menu after deletion
        elif choice == "5":
            print("Logging out... Have a great day!")
            break
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    main()
