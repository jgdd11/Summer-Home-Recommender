import pwinput
import users
import recommender

def login():
    username = input("Enter your username: ")
    password = pwinput.pwinput("Enter your password: ", mask="*")
    return [username, password]

