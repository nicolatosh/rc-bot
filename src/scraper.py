import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebElement, WebDriver
from selenium import webdriver
from typing import Any

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def _get_driver() -> WebDriver:
    """
    Get a driver instance for scraping.
    :return: WebDriver instance
    """
    # instantiate options for Chrome
    options = webdriver.ChromeOptions()

    # run the browser in headless mode
    options.add_argument("--headless=new")
    options.add_argument("--charset=utf-8")

    # instantiate Chrome WebDriver with options
    return webdriver.Chrome(options=options)

def _extract_pagination_counter(driver) -> int:
    """
    Extract pagination counter e.g the total number of pages.
    The default pages of RC blog must have been scraped
    by the driver. Check URL_BY_TYPE
    :param driver: Selenium webdriver
    :return: the number of pages of RC blog for monologues
    """
    tags: list[WebElement] = driver.find_elements(By.TAG_NAME, "a")
    pages = []
    for tag in tags:
        if "PaginationLinkUi" in tag.get_attribute("class"):
            text = tag.text
            if text is not None and text != "":
                pages.append(text)
    return max([int(p) for p in pages])


def get_total_pagination_counter(url: str) -> int:
    """
    Returns the total number of pages of the blog for monologues.
    :param driver: Selenium webdriver
    :return: total number of pages
    """

    driver = _get_driver()
    # open the specified URL in the browser
    driver.get(url)

    # get the previous height value
    last_height = driver.execute_script("return document.body.scrollHeight")
    logger.info("SCRAPER - Waiting page to be loaded")
    while True:
        # scroll down to the bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # wait for the page to load
        time.sleep(2)

        # get the new height and compare it with the last height
        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == last_height:
            # extract data once all content has loaded
            total_pages = _extract_pagination_counter(driver)
            break
        last_height = new_height

    # close the browser
    driver.quit()
    return total_pages


def _monologue_scraper(driver) -> list[dict[str, Any]]:
    """
    Creates monolgoues entrys for the database.
    Each entry has an URL and TEXT.
    The URL is the link of the RC blog for the monologue
    The TEXT is the name of the RC blog article aka the name of the monologue
    :param driver: Selenium webdriver
    :return: list of dicts
    """
    # find monologues using tag "a"
    tags = driver.find_elements(By.TAG_NAME, "a")
    scraped_data = []

    # iterate over found elements
    for blog_post in tags:

        # avoid to grab links with no title
        if blog_post.text is None or blog_post.text == "":
            continue

        # avoid to grab bad links, only monologue posts should be taken
        if "BlogPostAnnounceHeaderLinkUi" not in blog_post.get_attribute("class"):
            continue

        blog_post_url = blog_post.get_attribute("href")
        blog_post_name = blog_post.text

        data = {
            "url": blog_post_url,
            "text": blog_post_name,
        }

        # append the data to the empty list
        scraped_data.append(data)

    # return the scraped data
    return scraped_data


def async_monologue_scraper(url: str) -> list[Any]:

    logger.info(f"SCRAPER - Starting scraper at url [{url}]")

    # instantiate options for Chrome
    options = webdriver.ChromeOptions()

    # run the browser in headless mode
    options.add_argument("--headless=new")
    options.add_argument("--charset=utf-8")

    # instantiate Chrome WebDriver with options
    driver = webdriver.Chrome(options=options)

    # open the specified URL in the browser
    driver.get(url)

    # get the previous height value
    last_height = driver.execute_script("return document.body.scrollHeight")

    # array to collect scraped data
    blog_monologue_posts = []

    print("Waiting page to be loaded")
    while True:
        # scroll down to the bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # wait for the page to load
        time.sleep(2)

        # get the new height and compare it with the last height
        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == last_height:
            # extract data once all content has loaded
            blog_monologue_posts.extend(_monologue_scraper(driver))

            break
        last_height = new_height

    # close the browser
    driver.quit()
    logger.info(f"SCRAPER - Scraping of [{url}] done")
    return blog_monologue_posts
