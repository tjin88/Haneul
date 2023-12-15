from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
import time

options = Options()
options.headless = True

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def scrape_main_page(url):
    """
    Scrapes the main listing page for book URLs using Selenium.

    Args:
    url (str): URL of the main listing page.

    Returns:
    list: A list of tuples containing book titles and their URLs.
    """
    driver.get(url)
    time.sleep(5)  # adjust as necessary for page loading

    books = []
    book_elements = driver.find_elements(By.CLASS_NAME, 'novel-item')
    for element in book_elements:
        title_element = element.find_element(By.CLASS_NAME, 'novel-title')
        title = title_element.text.strip()
        book_url = title_element.find_element(By.TAG_NAME, 'a').get_attribute('href')
        books.append((title, book_url))

    return books

def scrape_book_details(title, book_url):
    """
    Scrapes detailed information about a book from its individual page using Selenium.
    
    Args:
    title (str): Title of the book.
    book_url (str): URL of the book's detail page.
    
    Returns:
    dict: A dictionary containing key details of the book.
    """
    driver.get(book_url)
    time.sleep(5)  # adjusted for page loading

    synopsis = driver.find_element(By.CSS_SELECTOR, '.summary .content').text.strip()
    author = driver.find_element(By.CSS_SELECTOR, '.author').text.replace('Author:', '').strip()
    updated_on = driver.find_element(By.CSS_SELECTOR, 'nav.content-nav p.update').text.strip()
    newest_chapter = driver.find_element(By.CSS_SELECTOR, 'nav.content-nav p.latest').text.strip()
    genres = [genre.text.strip() for genre in driver.find_elements(By.CSS_SELECTOR, 'div.categories a')]
    image_url = driver.find_element(By.CSS_SELECTOR, 'figure.cover img').get_attribute('src')
    rating = driver.find_element(By.CSS_SELECTOR, 'div.rating-star strong').text.strip()
    status = driver.find_element(By.CSS_SELECTOR, 'div.header-stats strong.ongoing').text.strip()
    
    try:
        followers_element = driver.find_element(By.CSS_SELECTOR, 'div.header-stats span:nth-of-type(3) strong')
        followers = followers_element.text.strip() if followers_element else 'Not Available'
    except NoSuchElementException:
        followers = 'Not Available'

    # Navigate to the chapters page
    chapters_url = f'{book_url}/chapters'
    driver.get(chapters_url)
    time.sleep(5)  # adjusted for page loading

    chapters = {}
    chapter_elements = driver.find_elements(By.CSS_SELECTOR, 'ul.chapter-list a')
    for chapter in chapter_elements:
        # Adjust chapter to look prettier :)
        parts = chapter.text.strip().split('\n')
        new_key = f'{parts[0]} - {parts[1]}'
        chapter_link = chapter.get_attribute('href')
        chapters[new_key] = chapter_link

    book_details = {
        'title': title,
        'synopsis': synopsis,
        'author': author,
        'artist': "None",
        'released_by': "None",
        'serialization': "None",
        'posted_by': "None",
        'posted_on': "placeholder to be found", # TODO: Find the original data posted
        'updated_on': updated_on, # ** This is a different format than AsuraScans **
        'newest_chapter': newest_chapter,
        'genres': genres,
        'image_url': image_url,
        'rating': rating,
        'status': status,
        'followers': followers,
        'chapters': chapters
    }

    return book_details

if __name__ == "__main__":
    base_url = 'https://lightnovelpub.vip'
    main_url = f'{base_url}/browse/genre-all-25060123/order-updated/status-all'
    books = scrape_main_page(main_url)

    for title, url in books:
        details = scrape_book_details(title, url)
        print("details", details)
        # TODO: Process/store details --> push to Database and all

    driver.quit()
