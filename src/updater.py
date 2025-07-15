import json, links
import logging
import time
import argparse
from datetime import datetime
from time import sleep

from celery_app import app
from const import DbType, URL_BY_TYPE
from scraper import async_monologue_scraper, get_total_pagination_counter

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def check_outdated_db(timestamp: datetime = None, schema_name: str = DbType.MALE.value) -> bool:
    """
    Check if the database is up to date based on the timestamp.
    :param timestamp:
    :param schema_name: Which schema to use either DBType.MALE or DBType.FEMALE values
    :return: True or False
    """
    if timestamp is None:
        timestamp = datetime.now()

    with open('database.json') as db:
        database = json.load(db)

    db_last_update_date = datetime.strptime(database[schema_name]["last_update"], '%d/%m/%Y')
    if timestamp > db_last_update_date:
        print(f'Database is outdated. Last update on [{db_last_update_date}] requested update by [{timestamp}]')
        return True
    else:
        print("Database is up to date")
        return False


def update_monologues_by_page(schema_name: DbType, page_number: int = 0):
    """
    Update the monologues database given schema name and page number.
    :param schema_name: Database schema name either DBType.MALE or DBType.FEMALE
    :param page_number: The RC blog pagination number e.g the "page" query param
    :return: None
    """

    url = URL_BY_TYPE[schema_name]

    # creating link for update monologues of a specific page
    page_url = url + f"?page={page_number}"

    # call scraper
    blog_posts = async_monologue_scraper(page_url)

    with open('database.json') as db:
        database = json.load(db)

    monologue_list = database[schema_name]["list"]
    monologue_names = [e["text"] for e in database[schema_name]["list"]]

    # updating monologues avoiding duplicates
    blog_posts = [b for b in blog_posts if b['text'] is not None and b['text'] != ""]
    for blog_post in blog_posts:
        if not blog_post["text"] in monologue_names:
            monologue_list.append(blog_post)

    # updating db
    if url == links.MALE_MONOLOGUES:
        database['male_monologues']["list"] = monologue_list
    else:
        database['female_monologues']["list"] = monologue_list

    # saving updates
    with open('database.json', 'w') as db:
        json.dump(database, db)

    logger.info(f'Done. Updated monologues database for {schema_name}')


@app.task
def update_monologues(schema_name: DbType) -> None:
    """
    Async Task.
    Update the monologues database given schema name.
    Updates the monologues of a schema so either Male or Female
    monologues parsing RC blog posts.
    Since blog posts are paginated, this function automatically
    select the subset of pages to scrape.

    The RC blog has the most recent articles at page 0.
    The bot parses the required pages up to the latest saved monologue.
    :param schema_name: Either DBType.MALE or DBType.FEMALE
    :return: None
    """

    logger.info(f'UPDATER - Updating monologues database for {schema_name}')
    # Checking last DB update to understand how many
    # pages of the Blog to parse
    url = URL_BY_TYPE[schema_name]

    # The current RC blog pages for monologues
    total_pages = get_total_pagination_counter(url)

    with open('database.json') as db:
        database = json.load(db)

    # How many pages have been already scraped in the past
    total_db_pages = database[schema_name]['total_pages']

    # Calculating delta e.g how many pages of the blog to scrape
    delta = total_pages - total_db_pages

    if delta == 0:
        if check_outdated_db(timestamp=datetime.now(), schema_name=schema_name):
            logger.info(f"Delta is 0 but database is outdated. Last update on {database[schema_name]['last_update']}. Updating only page 0")
        else:
            logger.info("Nothing to do. Database is up to date")
            return

    logger.info(f"Pages to be scraped [{delta}] ")

    # Updating from page 0 to delta
    for index in range(0, delta + 1):
        update_monologues_by_page(schema_name=schema_name, page_number=index)
        time.sleep(3)

    # Reopen updated db
    with open('database.json') as db:
        database = json.load(db)

    # updating total pages in db
    database[schema_name]['total_pages'] = total_pages

    # Setting date of last update
    database[schema_name]["last_update"] = datetime.now().strftime('%d/%m/%Y')

    # saving updates
    with open('database.json', 'w') as db:
        json.dump(database, db)


def main_parser() -> int:
    """
    Command line argument parsing for the UPDATE method.
    :return: 0 for success, -1 for failure.
    """
    # Create an ArgumentParser object with a description
    parser = argparse.ArgumentParser(description='Update the monologues database.')
    # Define command-line arguments
    parser.add_argument('dbtype',
                        type=str,
                        help='The type of schema. Use either "female_monologues" or "male_monologues" or "all" for both')
    parser.add_argument('--schedule',
                        type=int,
                        required=False,
                        help='Schedule the update after N minutes. Must be between 1 and 60. For'
                             'advanced scheduling, switch to queue mechanism. This command cannot'
                             'manage multiple schedules.',
                        default=0)
    # Parse the command-line arguments
    args = parser.parse_args()

    update_all = False
    if args.dbtype == "all":
        update_all = True
    elif args.dbtype not in [e.value for e in DbType]:
        logger.error(f'Unknown database type: [{args.dbtype}]')
        return -1

    minutes = 0
    if args.schedule:
        try:
            minutes = int(args.schedule)
            if minutes < 1 or minutes > 60:
                logger.error(f'Invalid schedule argument: [{args.schedule}]')
                return -1
        except ValueError:
            logger.error(f'Invalid schedule argument: [{args.schedule}]')
            return -1

    if minutes != 0:
        logger.info(f'Waiting for [{minutes}] minutes.')
        sleep(minutes)

    # Check if need to update all
    if update_all:
        logger.info(f'Request to update monologues for all schemas.')
        for e in [v.value for v in DbType]:
            update_monologues(schema_name=e)
    else:
        update_monologues(schema_name=args.dbtype)
    return 0

if __name__ == '__main__':
    main_parser()