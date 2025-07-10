import json

from const import DbType
from monologue import Monologue


def search_monologue(schema_type: DbType, search_string: str = "") -> set[Monologue]:

    with open("database.json", "r") as db:
        database = json.load(db)
        database = database[str(schema_type.value)]

    results = set()

    # By default, make no sense to look for everything
    # at least not in this method yet
    if search_string == "":
        return set()

    monologues = set([Monologue.from_dict(elem) for elem in database["list"]])
    for monologue in monologues:
        if search_string.casefold() in monologue.text.casefold():
            results.add(monologue)

    return results if len(results) else set()
