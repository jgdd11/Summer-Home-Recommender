import getpass
import users
import recommender

def login():
    username = input("Enter your username: ")
    password = getpass.getpass("Enter your password: ")
    return [username, password]
