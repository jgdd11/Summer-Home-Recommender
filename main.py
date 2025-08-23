from users import UserManager
from properties import PropertiesController
#comments

def main():
    manager = UserManager()
    logged_in_user = manager.login()

    # If login failed, exit the program
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
            
            # ---------------- Reservation Manager ----------------
            if choice1 == "1":
                print("Here is a list of your current reservations:")
                logged_in_user.view_reservations()

                # Reservation management submenu
                print("Please choose from the following options:")
                print("1. Make reservation")
                print("2. Delete Reservation")
                print("3. Go Back")
                print("4. Logout")

                choice2 = input("Choose an option: ").strip()
                if choice2 == "1":
                    logged_in_user.get_recommendations(manager)
                elif choice2 == "2":
                    logged_in_user.delete_reservation(manager)
                elif choice2 == "3":
                    break
                elif choice2 == "4":
                    print("Logging out...")
                    logout = True
                    break
                else:
                    print("Invalid choice. Try again.")

            # ---------------- Account Manager ----------------
            elif choice1 == "2":
                print("Please choose from the following options:")
                print("1: View account details")
                print("2. Change username")
                print("3. Change email")
                print("4. Change password")
                print("5. Change preferences")
                print("6. Delete account")
                print("7. Go Back")
                print("8. Logout")

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
                    logged_in_user.set_preferences()
                    manager.save_users
                elif choice3 == "6":
                    deleted = logged_in_user.delete_user(manager)
                    if deleted:
                        logout = True
                        break
                elif choice3 == "7":
                    break
                elif choice3 == "8":
                    print("Logging out...")
                    logout = True
                    break
                else:
                    print("Invalid choice. Try again.")

            # ---------------- Logout (from main menu) ----------------
            elif choice1 == "3":
                logout = True
                break
            else:
                print("Invalid choice. Try again.")
        if logout:
            break
    

if __name__ == "__main__":
    main()
