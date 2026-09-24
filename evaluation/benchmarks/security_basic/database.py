def find_user(cursor, username):
    query = f"SELECT * FROM users WHERE name = '{username}'"
    return cursor.execute(query).fetchone()


def find_user_safely(cursor, username):
    return cursor.execute(
        "SELECT * FROM users WHERE name = ?",
        (username,),
    ).fetchone()
