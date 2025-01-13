import asyncio
import os

from dotenv import load_dotenv

from utils.database_connector import DatabaseConnector

if ".env" in os.listdir("."):
    load_dotenv(".env")
from config import *

database = DatabaseConnector(DB_CONNECTION_STRING)


def validate_int(string: str) -> bool:
    try:
        int(string)
        return True
    except ValueError:
        return False


def infinite_input_int(prompt: str, min_int: int, max_int: int) -> int | None:
    while True:
        value = input(prompt)
        if validate_int(value):
            if min_int <= int(value) <= max_int:
                return int(value)
            else:
                print(f"Enter a number between {min_int} and {max_int} inclusive")
        else:
            print("Enter a number")


def infinite_input_str(prompt: str) -> str:
    while True:
        value = input(prompt)
        if len(value.strip()) > 0 and len(value.rstrip()) > 0:
            return value.strip().rstrip()


def infinite_input_yes_no(prompt: str) -> bool:
    while True:
        value = input(prompt)
        if value.lower() == "yes" or value.lower() == "y":
            return True
        elif value.lower() == "no" or value.lower() == "n":
            return False


def add_user():
    username = infinite_input_str("username> ")
    password = infinite_input_str("password> ")
    if not asyncio.run(database.is_exists(username)):
        asyncio.run(database.create_user(username, password))
        print("User created successfully")
    else:
        print("The user already exists")


def reset_user_pass():
    usernames = asyncio.run(database.get_usernames())
    for username_idx in range(len(usernames)):
        print(f"{username_idx + 1}. {usernames[username_idx]}")
    user_id = infinite_input_int("User number> ", 1, len(usernames))
    password = infinite_input_str("password> ")
    asyncio.run(database.change_password(usernames[user_id - 1], password))


def remove_user():
    usernames = asyncio.run(database.get_usernames())
    for username_idx in range(len(usernames)):
        print(f"{username_idx + 1}. {usernames[username_idx]}")
    user_id = infinite_input_int("User number> ", 1, len(usernames))
    if infinite_input_yes_no("are you sure? [y/n]> "):
        asyncio.run(database.remove_user(usernames[user_id - 1]))


def main():
    while True:
        print("1. Add user")
        print("2. Change user password")
        print("3. Delete user")
        print("4. Exit")
        action = infinite_input_int("> ", 1, 4)
        actions = [add_user, reset_user_pass, remove_user, exit]
        actions[action - 1]()


if __name__ == "__main__":
    main()
