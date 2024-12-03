from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import logging

# Set up the Selenium WebDriver
options = webdriver.ChromeOptions()
# options.add_argument('--headless')
options.add_argument('--disable-gpu')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Setting up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def scrape_with_selenium(url):
    driver.get(url)
    time.sleep(8)  # Wait for the page to load
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    return soup

# Example usage
url = 'https://rizzfables.com/series'
soup = scrape_with_selenium(url)

# Extracting book titles and URLs
book_elements = soup.select('div.bsx > a')
books = {}
for element in book_elements:
    title = element.get('title', '').strip()
    book_url = element.get('href', '')
    if title and book_url:
        normalized_title = title.replace("'", "’")
        books[normalized_title] = book_url

# Quit the driver
driver.quit()

# Print the results
for title, book_url in books.items():
    print(f"{title}: {book_url}")
