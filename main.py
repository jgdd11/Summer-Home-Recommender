from users import UserManager

def main():
    manager = UserManager()
    logged_in_user = manager.login()
    if not logged_in_user:
        print("No user logged in.")
        return

    while True:
        print(f"\nWelcome, {logged_in_user.name}!")
        print("1. Change username")
        print("2. Change email")
        print("3. Change password")
        print("4. Delete account")
        print("5. Logout")

        choice = input("Choose an option: ").strip()
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
            print("Logging out...")
            break
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    main()
