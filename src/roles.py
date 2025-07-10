import json

ROLES_FILE = "roles.json"

def load_roles():
    try:
        with open(ROLES_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_roles(roles):
    with open(ROLES_FILE, "w") as f:
        json.dump(roles, f)

user_roles = load_roles()

def get_role(user_id):
    return user_roles.get(str(user_id), "user")

def set_role(user_id, role):
    user_roles[str(user_id)] = role
    save_roles(user_roles)

def is_creator(user_id):
    return get_role(user_id) == "creator"

def is_admin_or_creator(user_id):
    return get_role(user_id) in ["admin", "creator"]
