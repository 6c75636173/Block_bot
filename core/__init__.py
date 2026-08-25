from .database import load_data, save_data

USERS_FILE = "data/users.json"
DAILY_FILE = "data/daily.json"


def _new_user_data():
    return {
        "xp": 0,
        "niveau": 1,
        "pieces": 100,
        "messages": 0,
        "inventaire": [],
    }


class UserData(dict):
    def __missing__(self, user_id):
        user_data = _new_user_data()
        self[user_id] = user_data
        return user_data


users_data = UserData(load_data(USERS_FILE))
daily_data = load_data(DAILY_FILE)


def get_user_data(user_id):
    user_id = str(user_id)
    users_data[user_id]
    user_data = users_data[user_id]
    user_data.setdefault("pieces", 100)
    user_data.setdefault("inventaire", [])
    return user_data
