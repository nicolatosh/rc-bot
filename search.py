import json

from const import DbType


def search_monologue(schema_type: DbType, search_string: str = "") -> list:

    with open("database.json", "r") as db:
        database = json.load(db)
        database = database[str(schema_type.value)]

    results = []

    # By default, make no sense to look for everything
    # at least not in this method yet
    if search_string == "":
        return []

    for monologue in database["list"]:
        if search_string.casefold() in monologue['text'].casefold():
            results.append(monologue)

    return results if len(results) else []
