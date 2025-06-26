import time
from selenium.webdriver.common.by import By
from selenium import webdriver
from typing import List, Dict


def _monologue_scraper(driver):
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


def async_monologue_scraper(url: str) -> List[Dict]:
    print(f"Starting scraper at url [{url}]")

    # instantiate options for Chrome
    options = webdriver.ChromeOptions()

    # run the browser in headless mode
    options.add_argument("--headless=new")

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
    print(f"Scraping of [{url}] done")
    return blog_monologue_posts
