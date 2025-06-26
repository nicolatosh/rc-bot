import json, links
from datetime import datetime

from const import DbType, URL_BY_TYPE
from scraper import async_monologue_scraper


def check_outdated_db(timestamp: datetime = None, schema_name: str = "male_monologues") -> bool:
    """
    :param timestamp:
    :type timestamp:
    :param schema_name: "male_monologues" or "female_monologues"
    :type schema_name: str
    :return:
    :rtype: True if db needs to be updated
    """
    if timestamp is None:
        timestamp = datetime.now()

    with open('database.json') as db:
        database = json.load(db)

        db_last_update_date = datetime.fromisoformat(database["last_update"])
        if timestamp > db_last_update_date:
            print(f'Database is outdated. Last update on [{db_last_update_date}] requested update by [{timestamp}]')
            return True
        else:
            print("Database is up to date")
            return False


def update_monologues_by_page(schema_name: DbType, page_number: int = 0):

    url = URL_BY_TYPE[schema_name]
    print(f"Updating monologues at url [{url}] page [{page_number}]")

    # creating link for update monologues of a specific page
    url = url + f"?page={page_number}"

    # call scraper
    blog_posts = async_monologue_scraper(url)

    with open('database.json') as db:
        database = json.load(db)
        monologue_list = database[schema_name]

    blog_posts = [b for b in blog_posts if b['text'] is not None and b['text'] != ""]
    for blog_post in blog_posts:
        monologue_list["list"].append(blog_post)

    # Setting date of last update
    monologue_list["last_update"] = datetime.now().strftime('%d/%m/%Y')

    # updating db
    if url == links.MALE_MONOLOGUES:
        database['male_monologues'] = monologue_list
    else:
        database['female_monologues'] = monologue_list

    # saving updates
    with open('database.json', 'w') as db:
        json.dump(database, db)

    print("Update done")