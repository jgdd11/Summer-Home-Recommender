from users import UserManager
from properties import PropertiesController

def main():
    manager = UserManager()
    logged_in_user = manager.login()
    if not logged_in_user:
        print("No user logged in.")
        return

    while True:
        logout = False
        print(f"\nWelcome, {logged_in_user.name}!")
        while True:
            print("Select an option from the following:")
            print("1. Reservation Manager")
            print("2. Account Manager")
            print("3. Logout")
            choice1 = input("Choose an option: ").strip()
            if choice1 == "1":
                print("Please choose from the following options:")
                print("1. Make reservation")
                print("2. Delete Reservation")
                print("3. View reservations")
                print("4. Go Back")
                print("5. Logout")

                choice2 = input("Choose an option: ").strip()
                if choice2 == "1":
                elif choice2 == "2":
                elif choice2 == "3":
                    logged_in_user.view_reservations()
                elif choice2 == "4":
                    break
                elif choice2 == "5":
                    print("Logging out...")
                    logout = True
                    break
                else:
                    print("Invalid choice. Try again.")

            elif choice1 == "2":
                print("Please choose from the following options:")
                print("1: View account details")
                print("2. Change username")
                print("3. Change email")
                print("4. Change password")
                print("5. Delete account")
                print("6. Go Back")
                print("7. Logout")

                choice3 = input("Choose an option: ").strip()
                if choice3 == "1":
                    logged_in_user.view_account_details()
                elif choice3 == "2":
                    logged_in_user.set_username(manager.userdb)
                    manager.save_users()
                elif choice3 == "3":
                    logged_in_user.set_email(manager.userdb)
                    manager.save_users()
                elif choice3 == "4":
                    logged_in_user.set_password()
                    manager.save_users()
                elif choice3 == "5":
                    deleted = manager.delete_user(logged_in_user)
                    if deleted:
                        break
                elif choice3 == "6":
                    break
                elif choice3 == "7":
                    print("Logging out...")
                    logout = True
                    break
                else:
                    print("Invalid choice. Try again.")
            else:
                print("Invalid choice. Try again.")
        if logout:
            break

if __name__ == "__main__":
    main()
