import sqlite3
import os


def get_user(user_id):
    conn = sqlite3.connect("users.db")

    query = f"SELECT * FROM users WHERE id = {user_id}"

    return conn.execute(query).fetchone()


def run_command(command):
    os.system(command)


def evaluate(expression):
    return eval(expression)