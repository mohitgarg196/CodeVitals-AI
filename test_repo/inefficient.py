def get_users(user_ids, db):
    users = []

    for user_id in user_ids:
        user = db.find_one({"id": user_id})
        users.append(user)

    return users